import subprocess
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
import platform
import os
import stat


SDK_URL = "https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip"

INSTALL_DIR = Path.home() / '.momo'/ "SDK" 
ZIP_FILE = INSTALL_DIR / "commandlinetools.zip"
CHECK_FILE = INSTALL_DIR / "cmdline-tools"


def progress(block_num, block_size, total_size):
    ''' A simple Progress Bar'''
    downloaded = block_num * block_size

    if total_size > 0:
        percent = min(downloaded / total_size * 100, 100)
        mb = downloaded / 1024 / 1024
        total = total_size / 1024 / 1024

        print(f"\rDownloading... {percent:5.1f}% ({mb:.1f}/{total:.1f} MB)", end="")


def install_android_cmdline_tools():
    ''' Main installer'''
    if CHECK_FILE.exists():
        print("Android command-line tools already installed.")
        return

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    print("Downloading Android command-line tools...")

    if platform.system != "Linux":
        raise NotImplementedError("Only Works in linux at the moment")

    urlretrieve(
        SDK_URL,
        ZIP_FILE,
        reporthook=progress
    )

    print("\nExtracting...")

    with zipfile.ZipFile(ZIP_FILE, "r") as z:
        z.extractall(INSTALL_DIR)

    ZIP_FILE.unlink()

    print("Done!")
    print("Installed to:", INSTALL_DIR)
    print("Installing required Tools")


def install_ndk():
    if (INSTALL_DIR / 'ndk').exists():
        print(" NDK already installed")
        return

    sdkmanager_file = CHECK_FILE / 'bin' / 'sdkmanager'

    os.chmod(
            sdkmanager_file,
            os.stat(sdkmanager_file).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )
    try:
        subprocess.run(
    [
        str(sdkmanager_file),
        "ndk;26.1.10909125",
        f"--sdk_root={INSTALL_DIR}",
    ],
    check=True,
)
        print("Installed NDK Tools")
    except FileNotFoundError as ex:
        print(ex)
                            
def install_build_tools():
    if (INSTALL_DIR / 'build-tools').exists():
        print("Build Tools already installed")
        return

    sdkmanager_file = CHECK_FILE / 'bin' / 'sdkmanager'

    os.chmod(
            sdkmanager_file,
            os.stat(sdkmanager_file).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
            )
    try:
        subprocess.run(
    [
        str(sdkmanager_file),
        "platform-tools",
        "platforms;android-34",
        "build-tools;34.0.0",
        f"--sdk_root={INSTALL_DIR}",
    ],
    check=True,
)
        print("Installed Build Tools")
    except FileNotFoundError as ex:
        print(ex)


def check_java():
    ''' Checks if OpenJDK 17 is there or not'''
    try:
        result = subprocess.run(
            ["java", "-version"],
            capture_output=True,
            text=True
        )

        output = result.stderr + result.stdout
        print(output)

        if '"17' in output: 
            return True

    except FileNotFoundError:
        pass

    return False


''' Checking if dependencies are there or not'''

# Dependency 1 - java
if not check_java():
    raise RuntimeError('''
    OpenJDK 17 is required. Its not installed or maybe the default one is set to other version of Java
    Install it and try again.
    
    Windows:
        winget install Microsoft.OpenJDK.17

    Ubuntu:
        sudo apt install openjdk-17-jdk

    Arch:
        sudo pacman -S jdk17-openjdk

    macOS:
        brew install openjdk@17
    ''')

# Dependency 2 - Android Command line tools
install_android_cmdline_tools()

# Dependency 3 - Android Command line build-tools
install_build_tools()

# Dependency 4 - NDK (Native Development Kit)
install_ndk()

