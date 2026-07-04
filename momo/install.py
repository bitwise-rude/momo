import subprocess
import shutil
import zipfile
import platform
import os
import stat
import sys
from pathlib import Path
from urllib.request import urlretrieve

# .momo is the home directory for all the permanently downloaded packages

MOMO_DIR = Path.home() / '.momo'
INSTALL_DIR = MOMO_DIR / "SDK"

# Platform-specific SDK urls
SDK_URLS = {
    "Linux": "https://dl.google.com/android/repository/commandlinetools-linux-14742923_latest.zip",
    "Darwin": "https://dl.google.com/android/repository/commandlinetools-mac-14742923_latest.zip",
    "Windows": "https://dl.google.com/android/repository/commandlinetools-win-14742923_latest.zip"
}

def progress(block_num, block_size, total_size):
    '''Terminal Progress Bar'''
    downloaded = block_num * block_size
    if total_size > 0:
        percent = min(downloaded / total_size * 100, 100)
        mb = downloaded / 1024 / 1024
        total = total_size / 1024 / 1024
        print(f"\rDownloading... {percent:5.1f}% ({mb:.1f}/{total:.1f} MB)", end="")

def nuke_and_reset():
    '''Clears everything to recover from corrupt files/bugs'''
    if MOMO_DIR.exists():
        print(f"Some unknown error occured because of which everything momo has downloaded will be nuked, please reinstall momo.")
        try:
            for root, dirs, files in os.walk(MOMO_DIR, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.chmod(filename, stat.S_IWUSR)
                    os.remove(filename)
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            shutil.rmtree(MOMO_DIR)
            print("Nuked Everything. Try Reinstalling momo")
        except Exception as e:
            print(f"Error purging directory: {e}. Please delete {MOMO_DIR} manually.")
            sys.exit(1)

def install_android_cmdline_tools():
    '''Downloads and structure fixes the SDK commandline-tools'''
    current_os = platform.system()
    if current_os not in SDK_URLS:
        raise RuntimeError(f"Unsupported Operating System: {current_os}")

    #NOTE: untested for windows
    CHECK_FILE = INSTALL_DIR / "cmdline-tools" / "latest" / "bin" / ("sdkmanager.bat" if current_os == "Windows" else "sdkmanager")
    if CHECK_FILE.exists():
        print("Android command-line tools already securely installed.")
        return

    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    ZIP_FILE = INSTALL_DIR / "commandlinetools.zip"

    print(f"Downloading Android command-line tools for {current_os}...")
    urlretrieve(SDK_URLS[current_os], ZIP_FILE, reporthook=progress)
    print("\nExtracting & fixing directory architecture...")

    # Extract temporary layout
    temp_extract = INSTALL_DIR / "temp_extract"
    with zipfile.ZipFile(ZIP_FILE, "r") as z:
        z.extractall(temp_extract)

    # Organize it to: SDK/cmdline-tools/latest/ because i found this to be the standard but somehow google forgot to do it 
    destination_folder = INSTALL_DIR / "cmdline-tools" / "latest"
    destination_folder.parent.mkdir(parents=True, exist_ok=True)
    
    if destination_folder.exists():
        shutil.rmtree(destination_folder)

    shutil.move(str(temp_extract / "cmdline-tools"), str(destination_folder))
    shutil.rmtree(temp_extract)
    ZIP_FILE.unlink()

    print("Successfully structured commandline tools layout.")

def run_sdk_tool(tool_name, arguments):
    '''Safely executes an SDK component dealing with OS variations'''
    current_os = platform.system()
    binary_name = f"{tool_name}.bat" if current_os == "Windows" else tool_name
    executable = INSTALL_DIR / "cmdline-tools" / "latest" / "bin" / binary_name

    if not executable.exists():
        raise FileNotFoundError(f"Could not locate required binary: {executable}")

    if current_os != "Windows":
        os.chmod(executable, os.stat(executable).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # automatically accepting lisence
    try:
        process = subprocess.Popen(
            [str(executable)] + arguments + [f"--sdk_root={INSTALL_DIR}"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate(input="y\ny\ny\ny\n")
        if process.returncode != 0:
            print(f"Error executing {tool_name}: {stderr}")
            raise subprocess.CalledProcessError(process.returncode, tool_name)
    except Exception as e:
        print(f"Execution failed: {e}")
        raise

def download_embeddedable_python():
    '''Fetches target production environment Python assets'''
    python_target_dir = MOMO_DIR / 'python'
    if python_target_dir.exists():
        print("Python environment setup verified.")
        return

    python_target_dir.mkdir(parents=True, exist_ok=True)
    print("Downloading Android runtime assets...")
    
    archive_name = "python.tar.gz"
    urlretrieve(
        "https://www.python.org/ftp/python/3.14.0/python-3.14.0-aarch64-linux-android.tar.gz",
        MOMO_DIR / archive_name,
        reporthook=progress
    )

    print("\nUnpacking runtime libraries...")
    try:
        shutil.unpack_archive(MOMO_DIR / archive_name, python_target_dir)
        (MOMO_DIR / archive_name).unlink()
        print("Done. Setup completed successfully.")
    except Exception as e:
        print(f"Failed to extract Python components: {e}")
        # Trigger an intentional error handling rollback if file corruption happens
        raise

def check_java():
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True)
        output = result.stderr + result.stdout
        return '"17' in output or ' 17.' in output
    except FileNotFoundError:
        return False

if __name__ == "__main__":
    # TODO: Chnage this to true if files got corrupted
    FORCE_NUKE = False 
    
    if FORCE_NUKE:
        nuke_and_reset()

    # dependency 1 : Java 17 (OpenJDK)
    if not check_java():
        print(" Error: OpenJDK 17 environment dependency missing.")
        sys.exit(1)

    # dependency 2: Android Command line Tools
    try:
        install_android_cmdline_tools()
        
        print("Configuring platforms and build environment pipelines (Might take a minute)...")
        run_sdk_tool("sdkmanager", ["platform-tools", "platforms;android-34", "build-tools;34.0.0"])
        
        print("Syncing Android Native Development Kit (NDK) (Might take a minute or two please wait...)")
        run_sdk_tool("sdkmanager", ["ndk;26.1.10909125"])

        # dependency 3: Embeddeable python 
        download_embeddedable_python()
        
    except Exception as error:
        print("Initiating cleanup fallback to prevent broken partial builds...")
        nuke_and_reset()
