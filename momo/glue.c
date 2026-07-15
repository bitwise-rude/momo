##include <jni.h>
#include <Python.h>
#include <android/log.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <wchar.h>

#define LOG(...) __android_log_print(ANDROID_LOG_DEBUG, "PythonBridge", __VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "PythonBridge", __VA_ARGS__)

// this will be accessed by others through extern, contains the app and jvm contexts

JavaVM*  g_jvm         = NULL;
jobject  g_app_context = NULL;   // NOTE: must be the Activity itself now, not
                                  // getApplicationContext() — setContentView()
                                  // only exists on Activity. See MainActivity.java.
static int g_python_ready = 0;
static char g_files_dir[512] = {0};

// COMPLEX_UNIT_SP, from android.util.TypedValue. Hardcoded here so we don't
// need to touch the TypedValue class just to read a constant.
#define COMPLEX_UNIT_SP 2

// ── UI handle table ─────────────────────────────────────────────────────────
// Widgets are never handed to Python as raw jobject pointers. Instead every
// created View gets a small int "handle" that indexes into these tables.
// This keeps the Python-facing API simple (plain ints) and lets us manage
// jobject global refs / callback refcounts in one place.
#define MAX_HANDLES 256
static jobject   g_views[MAX_HANDLES]     = {0};
static PyObject* g_callbacks[MAX_HANDLES] = {0};
static int       g_handle_count = 0;

static JNIEnv* get_env(void) {
    JNIEnv* env;
    (*g_jvm)->AttachCurrentThread(g_jvm, &env, NULL);
    return env;
}

static int store_handle(jobject local_view_ref) {
    if (g_handle_count >= MAX_HANDLES) {
        LOGE("store_handle: MAX_HANDLES (%d) exceeded", MAX_HANDLES);
        return -1;
    }
    JNIEnv* env = get_env();
    g_views[g_handle_count]     = (*env)->NewGlobalRef(env, local_view_ref);
    g_callbacks[g_handle_count] = NULL;
    return g_handle_count++;
}

static int handle_valid(int h) {
    return h >= 0 && h < g_handle_count && g_views[h] != NULL;
}

// Resolves a CSS-style color string ("#RRGGBB", "#AARRGGBB", or a named
// color like "red") to an Android color int via android.graphics.Color.
// Returns 1 on success (writes to *out), 0 on failure (Python exception set).
static int resolve_color(JNIEnv* env, const char* colorStr, jint* out) {
    jclass colorClass = (*env)->FindClass(env, "android/graphics/Color");
    jmethodID parseColor = (*env)->GetStaticMethodID(env, colorClass, "parseColor",
                                "(Ljava/lang/String;)I");
    jstring jcolor = (*env)->NewStringUTF(env, colorStr);
    (*env)->ExceptionClear(env); // clear any pending exception before we probe
    jint result = (*env)->CallStaticIntMethod(env, colorClass, parseColor, jcolor);

    if ((*env)->ExceptionCheck(env)) {
        (*env)->ExceptionClear(env);
        (*env)->DeleteLocalRef(env, jcolor);
        (*env)->DeleteLocalRef(env, colorClass);
        PyErr_Format(PyExc_ValueError, "invalid color string: %s", colorStr);
        return 0;
    }

    *out = result;
    (*env)->DeleteLocalRef(env, jcolor);
    (*env)->DeleteLocalRef(env, colorClass);
    return 1;
}

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
    JNIEnv* env = get_env();

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
    JNIEnv* env = get_env();

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

// ── More non-UI functions go here later: vibrate, notify, etc ──────────────


// ════════════════════════════════════════════════════════════════════════════
//  UI FUNCTIONS  — handle-based, so Python only ever sees plain ints.
//  All of these must be called on the UI thread. Right now that's true by
//  construction: initPython()/runScript() are called from onCreate() (UI
//  thread), and Android delivers click events on the UI thread too, so a
//  script that builds UI at top level and reacts to clicks via callbacks
//  never needs to hop threads. If you ever call runScript() from a
//  background thread, this breaks — you'd need runOnUiThread() from Java.
// ════════════════════════════════════════════════════════════════════════════

static PyObject* py_ui_create_label(PyObject* self, PyObject* args) {
    const char* text;
    if (!PyArg_ParseTuple(args, "s", &text)) return NULL;
    JNIEnv* env = get_env();

    jclass tvClass = (*env)->FindClass(env, "android/widget/TextView");
    jmethodID ctor = (*env)->GetMethodID(env, tvClass, "<init>", "(Landroid/content/Context;)V");
    jobject tv = (*env)->NewObject(env, tvClass, ctor, g_app_context);

    jmethodID setText = (*env)->GetMethodID(env, tvClass, "setText", "(Ljava/lang/CharSequence;)V");
    jstring jtext = (*env)->NewStringUTF(env, text);
    (*env)->CallVoidMethod(env, tv, setText, jtext);

    int handle = store_handle(tv);

    (*env)->DeleteLocalRef(env, jtext);
    (*env)->DeleteLocalRef(env, tv);
    (*env)->DeleteLocalRef(env, tvClass);

    if (handle < 0) { PyErr_SetString(PyExc_RuntimeError, "too many widgets"); return NULL; }
    return PyLong_FromLong(handle);
}

static PyObject* py_ui_create_button(PyObject* self, PyObject* args) {
    const char* text;
    if (!PyArg_ParseTuple(args, "s", &text)) return NULL;
    JNIEnv* env = get_env();

    jclass btnClass = (*env)->FindClass(env, "android/widget/Button");
    jmethodID ctor = (*env)->GetMethodID(env, btnClass, "<init>", "(Landroid/content/Context;)V");
    jobject btn = (*env)->NewObject(env, btnClass, ctor, g_app_context);

    jmethodID setText = (*env)->GetMethodID(env, btnClass, "setText", "(Ljava/lang/CharSequence;)V");
    jstring jtext = (*env)->NewStringUTF(env, text);
    (*env)->CallVoidMethod(env, btn, setText, jtext);

    int handle = store_handle(btn);
    if (handle < 0) {
        (*env)->DeleteLocalRef(env, jtext);
        (*env)->DeleteLocalRef(env, btn);
        (*env)->DeleteLocalRef(env, btnClass);
        PyErr_SetString(PyExc_RuntimeError, "too many widgets");
        return NULL;
    }

    // Wire up NativeClickListener(handle) so onClick() calls back into us.
    jclass listenerClass = (*env)->FindClass(env, "com/example/helloworld/NativeClickListener");
    jmethodID lctor = (*env)->GetMethodID(env, listenerClass, "<init>", "(I)V");
    jobject listener = (*env)->NewObject(env, listenerClass, lctor, (jint)handle);

    jclass viewClass = (*env)->FindClass(env, "android/view/View");
    jmethodID setOnClick = (*env)->GetMethodID(env, viewClass, "setOnClickListener",
                                "(Landroid/view/View$OnClickListener;)V");
    (*env)->CallVoidMethod(env, btn, setOnClick, listener);

    (*env)->DeleteLocalRef(env, jtext);
    (*env)->DeleteLocalRef(env, btn);
    (*env)->DeleteLocalRef(env, btnClass);
    (*env)->DeleteLocalRef(env, listener);
    (*env)->DeleteLocalRef(env, listenerClass);
    (*env)->DeleteLocalRef(env, viewClass);

    return PyLong_FromLong(handle);
}

static PyObject* py_ui_create_input(PyObject* self, PyObject* args) {
    const char* hint;
    if (!PyArg_ParseTuple(args, "s", &hint)) return NULL;
    JNIEnv* env = get_env();

    jclass etClass = (*env)->FindClass(env, "android/widget/EditText");
    jmethodID ctor = (*env)->GetMethodID(env, etClass, "<init>", "(Landroid/content/Context;)V");
    jobject et = (*env)->NewObject(env, etClass, ctor, g_app_context);

    jmethodID setHint = (*env)->GetMethodID(env, etClass, "setHint", "(Ljava/lang/CharSequence;)V");
    jstring jhint = (*env)->NewStringUTF(env, hint);
    (*env)->CallVoidMethod(env, et, setHint, jhint);

    int handle = store_handle(et);

    (*env)->DeleteLocalRef(env, jhint);
    (*env)->DeleteLocalRef(env, et);
    (*env)->DeleteLocalRef(env, etClass);

    if (handle < 0) { PyErr_SetString(PyExc_RuntimeError, "too many widgets"); return NULL; }
    return PyLong_FromLong(handle);
}

static PyObject* py_ui_create_layout(PyObject* self, PyObject* args) {
    const char* orientation;
    if (!PyArg_ParseTuple(args, "s", &orientation)) return NULL;
    JNIEnv* env = get_env();

    jclass llClass = (*env)->FindClass(env, "android/widget/LinearLayout");
    jmethodID ctor = (*env)->GetMethodID(env, llClass, "<init>", "(Landroid/content/Context;)V");
    jobject ll = (*env)->NewObject(env, llClass, ctor, g_app_context);

    jmethodID setOrientation = (*env)->GetMethodID(env, llClass, "setOrientation", "(I)V");
    jint orient = (strcmp(orientation, "horizontal") == 0) ? 0 : 1; // HORIZONTAL=0, VERTICAL=1
    (*env)->CallVoidMethod(env, ll, setOrientation, orient);

    int handle = store_handle(ll);

    (*env)->DeleteLocalRef(env, ll);
    (*env)->DeleteLocalRef(env, llClass);

    if (handle < 0) { PyErr_SetString(PyExc_RuntimeError, "too many widgets"); return NULL; }
    return PyLong_FromLong(handle);
}

static PyObject* py_ui_set_text(PyObject* self, PyObject* args) {
    int handle;
    const char* text;
    if (!PyArg_ParseTuple(args, "is", &handle, &text)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();
    jobject view = g_views[handle];

    // Works for TextView, Button, and EditText (all extend TextView).
    jclass viewClass = (*env)->GetObjectClass(env, view);
    jmethodID setText = (*env)->GetMethodID(env, viewClass, "setText", "(Ljava/lang/CharSequence;)V");
    jstring jtext = (*env)->NewStringUTF(env, text);
    (*env)->CallVoidMethod(env, view, setText, jtext);

    (*env)->DeleteLocalRef(env, jtext);
    (*env)->DeleteLocalRef(env, viewClass);
    Py_RETURN_NONE;
}

static PyObject* py_ui_get_text(PyObject* self, PyObject* args) {
    int handle;
    if (!PyArg_ParseTuple(args, "i", &handle)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();
    jobject view = g_views[handle];

    // getText() -> CharSequence, works for TextView/Button/EditText alike.
    // We then call toString() on whatever CharSequence impl comes back
    // (String for TextView/Button, Editable for EditText).
    jclass viewClass = (*env)->GetObjectClass(env, view);
    jmethodID getText = (*env)->GetMethodID(env, viewClass, "getText", "()Ljava/lang/CharSequence;");
    jobject charSeq = (*env)->CallObjectMethod(env, view, getText);

    jclass csClass = (*env)->GetObjectClass(env, charSeq);
    jmethodID toStringMethod = (*env)->GetMethodID(env, csClass, "toString", "()Ljava/lang/String;");
    jstring jresult = (jstring)(*env)->CallObjectMethod(env, charSeq, toStringMethod);

    const char* cresult = (*env)->GetStringUTFChars(env, jresult, NULL);
    PyObject* pyresult = PyUnicode_FromString(cresult);
    (*env)->ReleaseStringUTFChars(env, jresult, cresult);

    (*env)->DeleteLocalRef(env, jresult);
    (*env)->DeleteLocalRef(env, csClass);
    (*env)->DeleteLocalRef(env, charSeq);
    (*env)->DeleteLocalRef(env, viewClass);
    return pyresult;
}

static PyObject* py_ui_set_text_size(PyObject* self, PyObject* args) {
    int handle;
    float sp;
    if (!PyArg_ParseTuple(args, "if", &handle, &sp)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();
    jobject view = g_views[handle];

    jclass viewClass = (*env)->GetObjectClass(env, view);
    jmethodID setTextSize = (*env)->GetMethodID(env, viewClass, "setTextSize", "(IF)V");
    (*env)->CallVoidMethod(env, view, setTextSize, (jint)COMPLEX_UNIT_SP, (jfloat)sp);

    (*env)->DeleteLocalRef(env, viewClass);
    Py_RETURN_NONE;
}

static PyObject* py_ui_set_text_color(PyObject* self, PyObject* args) {
    int handle;
    const char* colorStr;
    if (!PyArg_ParseTuple(args, "is", &handle, &colorStr)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();

    jint color;
    if (!resolve_color(env, colorStr, &color)) return NULL;

    jobject view = g_views[handle];
    jclass viewClass = (*env)->GetObjectClass(env, view);
    jmethodID setTextColor = (*env)->GetMethodID(env, viewClass, "setTextColor", "(I)V");
    (*env)->CallVoidMethod(env, view, setTextColor, color);

    (*env)->DeleteLocalRef(env, viewClass);
    Py_RETURN_NONE;
}

static PyObject* py_ui_set_bg_color(PyObject* self, PyObject* args) {
    int handle;
    const char* colorStr;
    if (!PyArg_ParseTuple(args, "is", &handle, &colorStr)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();

    jint color;
    if (!resolve_color(env, colorStr, &color)) return NULL;

    // setBackgroundColor lives on View, so this works for layouts too.
    jobject view = g_views[handle];
    jclass viewClass = (*env)->GetObjectClass(env, view);
    jmethodID setBgColor = (*env)->GetMethodID(env, viewClass, "setBackgroundColor", "(I)V");
    (*env)->CallVoidMethod(env, view, setBgColor, color);

    (*env)->DeleteLocalRef(env, viewClass);
    Py_RETURN_NONE;
}

static PyObject* py_ui_set_onclick(PyObject* self, PyObject* args) {
    int handle;
    PyObject* callback;
    if (!PyArg_ParseTuple(args, "iO", &handle, &callback)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return NULL;
    }
    Py_XDECREF(g_callbacks[handle]);
    Py_INCREF(callback);
    g_callbacks[handle] = callback;
    Py_RETURN_NONE;
}

static PyObject* py_ui_add_view(PyObject* self, PyObject* args) {
    int parentHandle, childHandle;
    if (!PyArg_ParseTuple(args, "ii", &parentHandle, &childHandle)) return NULL;
    if (!handle_valid(parentHandle) || !handle_valid(childHandle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();
    jobject parent = g_views[parentHandle];
    jobject child  = g_views[childHandle];

    jclass lpClass = (*env)->FindClass(env, "android/widget/LinearLayout$LayoutParams");
    jmethodID lpCtor = (*env)->GetMethodID(env, lpClass, "<init>", "(II)V");
    jobject lp = (*env)->NewObject(env, lpClass, lpCtor, (jint)-2, (jint)-2); // WRAP_CONTENT x2

    jclass vgClass = (*env)->FindClass(env, "android/view/ViewGroup");
    jmethodID addView = (*env)->GetMethodID(env, vgClass, "addView",
                            "(Landroid/view/View;Landroid/view/ViewGroup$LayoutParams;)V");
    (*env)->CallVoidMethod(env, parent, addView, child, lp);

    (*env)->DeleteLocalRef(env, lp);
    (*env)->DeleteLocalRef(env, lpClass);
    (*env)->DeleteLocalRef(env, vgClass);
    Py_RETURN_NONE;
}

static PyObject* py_ui_show(PyObject* self, PyObject* args) {
    int handle;
    if (!PyArg_ParseTuple(args, "i", &handle)) return NULL;
    if (!handle_valid(handle)) {
        PyErr_SetString(PyExc_ValueError, "invalid widget handle");
        return NULL;
    }
    JNIEnv* env = get_env();
    jobject view = g_views[handle];

    // g_app_context must actually be the Activity for this to resolve.
    jclass actClass = (*env)->GetObjectClass(env, g_app_context);
    jmethodID setContentView = (*env)->GetMethodID(env, actClass, "setContentView", "(Landroid/view/View;)V");
    (*env)->CallVoidMethod(env, g_app_context, setContentView, view);

    (*env)->DeleteLocalRef(env, actClass);
    Py_RETURN_NONE;
}

// Called from NativeClickListener.onClick() -> nativeOnClick(handle)
JNIEXPORT void JNICALL
Java_com_example_helloworld_NativeClickListener_nativeOnClick(JNIEnv* env, jobject thiz, jint handle) {
    if (!handle_valid((int)handle)) return;
    PyObject* cb = g_callbacks[handle];
    if (!cb) return;

    PyObject* result = PyObject_CallObject(cb, NULL);
    if (!result) {
        LOGE("nativeOnClick: Python callback raised an exception");
        PyErr_Print();
    } else {
        Py_DECREF(result);
    }
}

static PyMethodDef AndroidMethods[] = {
    {"flash_on",         py_flash_on,         METH_NOARGS,  "Turn on flashlight"},
    {"flash_off",        py_flash_off,        METH_NOARGS,  "Turn off flashlight"},

    {"ui_create_label",  py_ui_create_label,  METH_VARARGS, "ui_create_label(text) -> handle"},
    {"ui_create_button", py_ui_create_button, METH_VARARGS, "ui_create_button(text) -> handle"},
    {"ui_create_input",  py_ui_create_input,  METH_VARARGS, "ui_create_input(hint) -> handle"},
    {"ui_create_layout", py_ui_create_layout, METH_VARARGS, "ui_create_layout('vertical'|'horizontal') -> handle"},
    {"ui_set_text",      py_ui_set_text,      METH_VARARGS, "ui_set_text(handle, text)"},
    {"ui_get_text",      py_ui_get_text,      METH_VARARGS, "ui_get_text(handle) -> text"},
    {"ui_set_text_size", py_ui_set_text_size, METH_VARARGS, "ui_set_text_size(handle, size_sp)"},
    {"ui_set_text_color",py_ui_set_text_color,METH_VARARGS, "ui_set_text_color(handle, color_str)"},
    {"ui_set_bg_color",  py_ui_set_bg_color,  METH_VARARGS, "ui_set_bg_color(handle, color_str)"},
    {"ui_set_onclick",   py_ui_set_onclick,   METH_VARARGS, "ui_set_onclick(handle, callback)"},
    {"ui_add_view",      py_ui_add_view,      METH_VARARGS, "ui_add_view(parent_handle, child_handle)"},
    {"ui_show",          py_ui_show,          METH_VARARGS, "ui_show(handle)"},

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
// ════════════════════════════════════════════════════════════════════════════

JNIEXPORT void JNICALL
Java_com_example_helloworld_MainActivity_initPython(
        JNIEnv* env, jobject thiz, jobject context, jstring jFilesDir) {

    if (g_python_ready) {
        LOG("initPython: already initialized, skipping");
        return;
    }

    // NOTE: `context` must be the Activity (pass `this` from Java), not
    // getApplicationContext() — the UI functions need setContentView().
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
}include <jni.h>
