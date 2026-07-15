#!/bin/python3

# Written by - Meyan

# NEVER RUN THE FILE ALWAYS CALL FROM SOMEWHERE ELSE

import os
import shutil
import inspect
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path

import pexpect


@dataclass
class Paths:
    project: Path
    momo: Path
    sdk: Path

    build: Path
    src: Path
    assets: Path
    lib: Path
    python: Path
    res: Path

    manifest: Path

    android_jar: Path
    build_tools: Path
    aapt2: Path
    d8: Path
    zipalign: Path
    apksigner: Path

    ndk: Path
    toolchain: Path
    sysroot: Path

    adb: Path

    apk_unsigned: Path
    apk_aligned: Path
    apk_signed: Path
    apk_base : Path


def _build_paths(project_dir):
    PROJECT = project_dir
    MOMO = PROJECT / ".momo"
    SDK = Path.home() / ".momo" / "SDK"

    BUILD = MOMO / "build"
    SRC = MOMO / "src"
    ASSETS = MOMO / "assets"
    LIB = MOMO / "lib"
    PYTHON = MOMO / "python"
    RES = MOMO / "res"

    MANIFEST = MOMO / "AndroidManifest.xml"

    ANDROID_JAR = SDK / "platforms" / "android-34" / "android.jar"
    BUILD_TOOLS = SDK / "build-tools" / "34.0.0"
    AAPT2 = BUILD_TOOLS / "aapt2"
    D8 = BUILD_TOOLS / "d8"
    ZIPALIGN = BUILD_TOOLS / "zipalign"
    APKSIGNER = BUILD_TOOLS / "apksigner"

    NDK = SDK / "ndk" / "26.1.10909125"
    TOOLCHAIN = NDK / "toolchains" / "llvm" / "prebuilt" / "linux-x86_64"
    SYSROOT = TOOLCHAIN / "sysroot"

    ADB = SDK / "platform-tools" / "adb"

    APK_UNSIGNED = BUILD / "app-unsigned.apk"
    APK_ALIGNED = BUILD / "aligned.apk"
    APK_SIGNED = BUILD / "app.apk"
    APK_BASE = BUILD / "app-base.apk"
    

    return Paths(
        project=PROJECT,
        momo=MOMO,
        sdk=SDK,
        build=BUILD,
        src=SRC,
        assets=ASSETS,
        lib=LIB,
        python=PYTHON,
        res=RES,
        manifest=MANIFEST,
        android_jar=ANDROID_JAR,
        build_tools=BUILD_TOOLS,
        aapt2=AAPT2,
        d8=D8,
        zipalign=ZIPALIGN,
        apksigner=APKSIGNER,
        ndk=NDK,
        toolchain=TOOLCHAIN,
        sysroot=SYSROOT,
        adb=ADB,
        apk_unsigned=APK_UNSIGNED,
        apk_aligned=APK_ALIGNED,
        apk_signed=APK_SIGNED,
        apk_base = APK_BASE
    )


def _resolve():
    #TODO: RESOLVING MAYBE BUGGY SOMETIMES FIX IT
    # This should resolve the current working directory to fix importing of the library ()

    return _build_paths(Path(os.getcwd()))

def add_file_to_apk(apk_path: Path, file_path: Path, arcname=None):
    if arcname is None:
        arcname = str(file_path)

    with zipfile.ZipFile(str(apk_path), 'a', compression=zipfile.ZIP_DEFLATED) as apk:
        apk.write(str(file_path), str(arcname))

def add_directory_to_apk(apk_path: Path, dir_path: Path, base_dir: Path):
    with zipfile.ZipFile(str(apk_path), 'a', compression=zipfile.ZIP_DEFLATED) as apk:
        for root, dirs, files in os.walk(str(dir_path)):
            for file in files:
                full_path = Path(root) / file
                arcname = full_path.relative_to(base_dir)
                apk.write(str(full_path), str(arcname))

def run(info, cmd, check=True):
    str_cmd = [str(part) for part in cmd]
    print("-------------------")
    print(f'{info}.....')
    subprocess.run(str_cmd, check=check)


def clean():
    p = _resolve()
    # TODO: do if only exists
    run(
        "Removing all apks, Ignore if any error persists, "
        "you can manually delete all the apks inside the build folder.",
        [
            "rm",
            p.apk_aligned,
            p.apk_signed,
            Path(str(p.apk_signed) + ".idsig"),
            p.apk_unsigned,
            p.build / "res.zip",
        ],
        check=False,
    )


def create_key(p: Paths):
    #TODO: ask user
    keystore = p.project / "mykey.jks"
    child = pexpect.spawn(
        f"keytool -genkeypair -v -keystore {keystore} -keyalg RSA "
        f"-keysize 2048 -validity 10000 -alias mykey"
    )

    child.expect("Enter keystore password:")
    child.sendline("mypassword")

    child.expect("Re-enter new password:")
    child.sendline("mypassword")

    child.expect("What is your first and last name?")
    child.sendline("My Name")

    child.expect("What is the name of your organizational unit?")
    child.sendline("Dev")

    child.expect("What is the name of your organization?")
    child.sendline("MyOrg")

    child.expect("What is the name of your City?")
    child.sendline("Kathmandu")

    child.expect("What is the name of your State?")
    child.sendline("Bagmati")

    child.expect("What is the two-letter country code?")
    child.sendline("NP")

    child.expect("Is CN=.* correct?")
    child.sendline("yes")

    child.wait()
    # run("Creating a Key since no key found",
    #     ["keytool", "-genkeypair", "-v", "-keystore", keystore, "-keyalg", "RSA", "-keysize", "2048",
    #      "-validity", "10000", "-alias", "mykey"])


def sign_key(p: Paths):
    keystore = p.project / "mykey.jks"
    child = pexpect.spawn(
        f"{p.apksigner} sign --ks {keystore} --out {p.apk_signed} {p.apk_aligned}"
    )
    child.expect("Keystore password for signer #1:")
    child.sendline("mypassword")
    child.wait()


def compile_python():
    p = _resolve()

    PYTHON_INCLUDE = p.python / "include" / "python3.14"
    PYTHON_LIB = p.python / "libs"

    native_out = p.lib / "arm64-v8a" / "libnative-lib.so"
    native_out.parent.mkdir(parents=True, exist_ok=True)

    run(
        "Compiling Native C + Python",
        [
            p.toolchain / "bin" / "clang",

            "--target=aarch64-linux-android21",

            f"--sysroot={p.sysroot}",

            "-shared", "-fPIC",

            p.src / "test.c",

            "-o", native_out,

            f"-I{p.sysroot / 'usr' / 'include'}",
            f"-I{p.sysroot / 'usr' / 'include' / 'aarch64-linux-android'}",

            f"-I{PYTHON_INCLUDE}",

            f"-L{PYTHON_LIB}",
            "-lpython3.14",

            "-llog",
            "-landroid",
        ],
    )


def lazy_clean(p: Paths):
    run("Lazy cleaning the aligned apk", ['rm', p.apk_aligned], check=False)


def uninstall(p: Paths):
    run("Uninstalling previous version", [p.adb, 'uninstall', 'com.example.helloworld'], check=False)

def quick_rebuild():
    p = _resolve()

    if not p.apk_base.exists():
        print("No base apk found. Please run build_python()")
        return

    uninstall(p)

    p.build.mkdir(parents=True, exist_ok=True)

    lazy_clean(p)  
    run("Removing stale unsigned apk", ["rm", "-f", p.apk_unsigned], check=False)

    print("Restoring base apk (dex + native libs, no assets)")
    shutil.copy(p.apk_base, p.apk_unsigned)

    print("Adding assets (your changed scripts + stdlib)")
    add_directory_to_apk(p.apk_unsigned, p.assets, base_dir=p.momo)

    run(
        "Align and flatten the output apk",
        [p.zipalign, "-v", "4", p.apk_unsigned, p.apk_aligned],
    )

    if not (p.project / "mykey.jks").exists():
        create_key(p)

    sign_key(p)

    run("Running ADB to install", [p.adb, 'install', p.apk_signed])

    run(
        "Opening App on Device",
        [p.adb, "shell", "monkey", "-p", "com.example.helloworld", "-c", "android.intent.category.LAUNCHER", "1"],
    )

def build_python():
    p = _resolve()

    lazy_clean(p)
    uninstall(p)

    p.build.mkdir(parents=True, exist_ok=True)

    run(
        "Compiling Java Code to Classes",
            ["javac", "-d", p.build,
            p.src / "MainActivity.java", p.src / "NativeClickListener.java",
            "-classpath", p.android_jar],
    )

    run(
        "Compiling .classes to .dex",
            [
            p.d8, "--output", p.build / "dex",
            "--lib", p.android_jar,
            p.build / "com" / "example" / "helloworld" / "MainActivity.class",
            p.build / "com" / "example" / "helloworld" / "NativeClickListener.class",
        ],
    )

    (p.build / "res").mkdir(parents=True, exist_ok=True)

    run(
        "Compiling resources",
        [p.aapt2, "compile", p.res / "values" / "strings.xml", "-o", p.build / "res" / ""],
    )

    ## TODO: important this resource things is stupid, maybe i don't even have to do that
    run(
        "Linking APK with manifest + assets",
        [
            p.aapt2, "link",
            "-o", p.apk_unsigned,
            "-I", p.android_jar,
            "--manifest", p.manifest,
            p.build / "res" / "values_strings.arsc.flat",
        ],
    )

    # run("Inject Dalvik Code",
    #     ["zip", "-j", p.apk_unsigned, p.build / "dex" / "classes.dex"])
    #
    #
    # run("Adding Python runtime library",
    # [ "zip", "-r", p.apk_unsigned, p.lib / "arm64-v8a" / "libpython3.14.so" ])
    #
    # run("Adding native libraries",
    # [ "zip", "-r", p.apk_unsigned, p.lib / "arm64-v8a" / "libnative-lib.so" ])
    #
    # run("Adding assets (Python stdlib)",
    # [ "zip", "-r", p.apk_unsigned, p.assets ])

    print("Inject Dalvik Code")
    add_file_to_apk(p.apk_unsigned, p.build / "dex" / "classes.dex", "classes.dex")

    print("Adding Python runtime library")
    add_file_to_apk(
        p.apk_unsigned,
        p.lib / "arm64-v8a" / "libpython3.14.so",
        "lib/arm64-v8a/libpython3.14.so",
    )

    print("Adding native libraries")
    add_file_to_apk(
        p.apk_unsigned,
        p.lib / "arm64-v8a" / "libnative-lib.so",
        "lib/arm64-v8a/libnative-lib.so",
    )

    print("Snapshotting base apk for quick rebuilds")
    shutil.copy(p.apk_unsigned, p.apk_base)


    print("Adding assets (Python stdlib)")
    add_directory_to_apk(p.apk_unsigned, p.assets, base_dir=p.momo)

    run(
        "Align and flatten the output apk",
        [p.zipalign, "-v", "4", p.apk_unsigned, p.apk_aligned],
    )

    if not (p.project / "mykey.jks").exists():
        create_key(p)

    sign_key(p)
    # run("Signing the key",
    #     [p.apksigner, "sign", "--ks", p.project / "mykey.jks", "--out", p.apk_signed, p.apk_aligned])

    run("Running ADB to install", [p.adb, 'install', p.apk_signed])

    run(
        "Opening App on Device",
        [p.adb, "shell", "monkey", "-p", "com.example.helloworld", "-c", "android.intent.category.LAUNCHER", "1"],
    )


def build():
    p = _resolve()

    lazy_clean(p)
    uninstall(p)

    p.build.mkdir(parents=True, exist_ok=True)

    run(
    "Compiling Java Code to Classes",
    ["javac", "-d", p.build,
     p.src / "MainActivity.java", p.src / "NativeClickListener.java",
     "-classpath", p.android_jar],
)

    run(
    "Compiling .classes to .dex",
    [
        p.d8, "--output", p.build / "dex",
        "--lib", p.android_jar,
        p.build / "com" / "example" / "helloworld" / "MainActivity.class",
        p.build / "com" / "example" / "helloworld" / "NativeClickListener.class",
    ],
)
    run(
        "Compiling Resources and stuff",
        [p.aapt2, "compile", "-o", p.build / "res.zip", p.res / "values" / "strings.xml"],
    )

    run(
        "Linking Everything without the dalvik Code",
        [
            p.aapt2, "link",
            "-o", p.apk_unsigned,
            "-I", p.android_jar,
            "--manifest", p.manifest,
            p.build / "res.zip",
        ],
    )

    run(
        "Inject Dalvik Code",
        ["zip", "-j", p.apk_unsigned, p.build / "dex" / "classes.dex"],
    )

    run(
        "Align and flatten the output apk",
        [p.zipalign, "-v", "4", p.apk_unsigned, p.apk_aligned],
    )

    if not (p.project / "mykey.jks").exists():
        create_key(p)

    sign_key(p)

    # run("Signing the key",
    #     [p.apksigner, "sign", "--ks", p.project / "mykey.jks", "--out", p.apk_signed, p.apk_aligned])

    run("Running ADB to install", [p.adb, 'install', p.apk_signed])

    run(
        "Opening App on Device",
        [p.adb, "shell", "monkey", "-p", "com.example.helloworld", "-c", "android.intent.category.LAUNCHER", "1"],
    )


