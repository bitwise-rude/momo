#include <jni.h>
#include <Python.h>
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>

#define LOG(...) __android_log_print(ANDROID_LOG_DEBUG, "PythonBridge", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "PythonBridge", __VA_ARGS__)

// this will be accessed by others through extern, contains the app and jvm contexts

JavaVM*  g_jvm         = NULL;
jobject  g_app_context = NULL;
static int g_python_ready = 0;
static char g_files_dir[512] = {0};

// Called when loadlibary is called
JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void* reserved) {
    g_jvm = vm;
    LOG("JNI_OnLoad: g_jvm stashed");
    return JNI_VERSION_1_6;
}


// ════════════════════════════════════════════════════════════════════════════
//  ANDROID MODULE  — lives here 
//  user does:  import android
//  for android module the following embedded C is used
// ════════════════════════════════════════════════════════════════════════════

static PyObject* py_flash_on(PyObject* self, PyObject* args) {
    if (!g_jvm || !g_app_context) {
        PyErr_SetString(PyExc_RuntimeError, "Bridge not initialized");
        return NULL;
    }
    JNIEnv* env;
    (*g_jvm)->AttachCurrentThread(g_jvm, &env, NULL);

    jclass    ctxClass       = (*env)->GetObjectClass(env, g_app_context);
    jmethodID getSysSvc      = (*env)->GetMethodID(env, ctxClass,
                                   "getSystemService",
                                   "(Ljava/lang/String;)Ljava/lang/Object;");
    jstring   camStr         = (*env)->NewStringUTF(env, "camera");
    jobject   camManager     = (*env)->CallObjectMethod(env, g_app_context, getSysSvc, camStr);

    jclass    camClass       = (*env)->GetObjectClass(env, camManager);
    jmethodID getCamIds      = (*env)->GetMethodID(env, camClass,
                                   "getCameraIdList", "()[Ljava/lang/String;");
    jobjectArray ids         = (jobjectArray)(*env)->CallObjectMethod(env, camManager, getCamIds);

    jstring   camId          = (jstring)(*env)->GetObjectArrayElement(env, ids, 0);
    jmethodID setTorch       = (*env)->GetMethodID(env, camClass,
                                   "setTorchMode", "(Ljava/lang/String;Z)V");
    (*env)->CallVoidMethod(env, camManager, setTorch, camId, JNI_TRUE);

    (*env)->DeleteLocalRef(env, camStr);
    (*env)->DeleteLocalRef(env, camId);
    LOG("flash_on called");
    Py_RETURN_NONE;
}

static PyObject* py_flash_off(PyObject* self, PyObject* args) {
    if (!g_jvm || !g_app_context) {
        PyErr_SetString(PyExc_RuntimeError, "Bridge not initialized");
        return NULL;
    }
    JNIEnv* env;
    (*g_jvm)->AttachCurrentThread(g_jvm, &env, NULL);

    jclass    ctxClass   = (*env)->GetObjectClass(env, g_app_context);
    jmethodID getSysSvc  = (*env)->GetMethodID(env, ctxClass,
                               "getSystemService",
                               "(Ljava/lang/String;)Ljava/lang/Object;");
    jstring   camStr     = (*env)->NewStringUTF(env, "camera");
    jobject   camManager = (*env)->CallObjectMethod(env, g_app_context, getSysSvc, camStr);

    jclass    camClass   = (*env)->GetObjectClass(env, camManager);
    jmethodID getCamIds  = (*env)->GetMethodID(env, camClass,
                               "getCameraIdList", "()[Ljava/lang/String;");
    jobjectArray ids     = (jobjectArray)(*env)->CallObjectMethod(env, camManager, getCamIds);

    jstring   camId      = (jstring)(*env)->GetObjectArrayElement(env, ids, 0);
    jmethodID setTorch   = (*env)->GetMethodID(env, camClass,
                               "setTorchMode", "(Ljava/lang/String;Z)V");
    (*env)->CallVoidMethod(env, camManager, setTorch, camId, JNI_FALSE);

    (*env)->DeleteLocalRef(env, camStr);
    (*env)->DeleteLocalRef(env, camId);
    LOG("flash_off called");
    Py_RETURN_NONE;
}

// ── More functions will be added here later like notification ,etc ,etc
// static PyObject* py_vibrate(...)  { ... } 
// static PyObject* py_notify(...)   { ... }

static PyMethodDef AndroidMethods[] = {
    {"flash_on",  py_flash_on,  METH_NOARGS,  "Turn on flashlight"},
    {"flash_off", py_flash_off, METH_NOARGS,  "Turn off flashlight"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef androidmodule = {
    PyModuleDef_HEAD_INIT,
    "android",       
    NULL,
    -1,
    AndroidMethods
};

PyMODINIT_FUNC PyInit_android(void) {
    return PyModule_Create(&androidmodule);
}


// ════════════════════════════════════════════════════════════════════════════
//  JNI ENTRY POINTS  — from MainActivity.java
//  For java as above
// ════════════════════════════════════════════════════════════════════════════

JNIEXPORT void JNICALL
Java_com_example_helloworld_MainActivity_initPython(
        JNIEnv* env, jobject thiz, jobject context, jstring jFilesDir) {

    if (g_python_ready) {
        LOG("initPython: already initialized, skipping");
        return;
    }

    g_app_context = (*env)->NewGlobalRef(env, context);

    const char* fd = (*env)->GetStringUTFChars(env, jFilesDir, NULL);
    snprintf(g_files_dir, sizeof(g_files_dir), "%s", fd);
    (*env)->ReleaseStringUTFChars(env, jFilesDir, fd);

    PyImport_AppendInittab("android", &PyInit_android);

    // python's configuration
    PyConfig config;
    PyConfig_InitPythonConfig(&config);

    wchar_t whome[512], wlib[512], wscripts[512];
    swprintf(whome,    512, L"%s/python",                      g_files_dir);
    swprintf(wlib,     512, L"%s/python/lib/python3.14",       g_files_dir);
    swprintf(wscripts, 512, L"%s/python/scripts",              g_files_dir);

    PyConfig_SetString(&config, &config.home, whome);
    config.module_search_paths_set = 1;
    PyWideStringList_Append(&config.module_search_paths, wlib);
    PyWideStringList_Append(&config.module_search_paths, wscripts);

    PyStatus status = Py_InitializeFromConfig(&config);
    PyConfig_Clear(&config);

    if (PyStatus_Exception(status)) {
        LOGE("initPython: Py_InitializeFromConfig FAILED");
        return;
    }

    g_python_ready = 1;
    LOG("initPython: Python %s ready", Py_GetVersion());
}

JNIEXPORT jstring JNICALL
Java_com_example_helloworld_MainActivity_runScript(
        JNIEnv* env, jobject thiz, jstring jScriptName) {

    if (!g_python_ready) {
        return (*env)->NewStringUTF(env, "error: python not initialized");
    }

    const char* scriptName = (*env)->GetStringUTFChars(env, jScriptName, NULL);

    char scriptPath[1024];
    snprintf(scriptPath, sizeof(scriptPath),
             "%s/python/scripts/%s", g_files_dir, scriptName);

    (*env)->ReleaseStringUTFChars(env, jScriptName, scriptName);

    FILE* fp = fopen(scriptPath, "r");
    if (!fp) {
        LOGE("runScript: file not found: %s", scriptPath);
        return (*env)->NewStringUTF(env, "error: script not found");
    }

    PyObject* main_module = PyImport_AddModule("__main__");
    PyObject* dict        = PyModule_GetDict(main_module);

    PyRun_SimpleFile(fp, scriptPath);
    fclose(fp);

    PyObject* result = PyDict_GetItemString(dict, "result");
    jstring ret;
    if (result && PyUnicode_Check(result)) {
        ret = (*env)->NewStringUTF(env, PyUnicode_AsUTF8(result));
    } else {
        LOGE("runScript: no 'result' variable found in script");
        ret = (*env)->NewStringUTF(env, "error: script must set result = '...'");
    }

    return ret;
}

