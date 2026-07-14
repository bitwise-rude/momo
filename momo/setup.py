import inspect
from pathlib import Path
import shutil


# REPLACE THIS WITH OS.CWD? TODO
caller_frame = inspect.stack()[1]
caller_dir = Path(caller_frame.filename).resolve().parent

momo_dir = caller_dir / ".momo"

module_dir = Path(__file__).resolve().parent

# Global Momo python installation 
momo_python = Path.home() / ".momo" / "python"

prefix = momo_python / "prefix"


if not momo_dir.exists():

    print("Initializing Momo project...")

    momo_dir.mkdir()

    folders = [
        "build",
        "build/dex",
        "assets/python/lib/python3.14",
        "assets/python/scripts",
        "lib/arm64-v8a",
        "python/include",
        "python/libs",
        "res/values",
        "src"
    ]

    for folder in folders:
        (momo_dir / folder).mkdir(parents=True, exist_ok=True)


    # Android Templates will be copied from modules directory #TODO: what to do when making actual module?

    shutil.copy2(
        module_dir / "AndroidManifest.xml",
        momo_dir / "AndroidManifest.xml"
    )

    shutil.copy2(
        module_dir / "MainActivity.java",
        momo_dir / "src/MainActivity.java"
    )

    shutil.copy2(
        module_dir / "glue.c",
        momo_dir / "src/test.c"
    )


    # python stuff copy from .momo in home

    shutil.copytree(
        prefix / "include",
        momo_dir / "python/include",
        dirs_exist_ok=True
    )

    libpython = list(prefix.rglob("libpython3.14.so"))

    if libpython:

        shutil.copy2(
            libpython[0],
            momo_dir / "python/libs/libpython3.14.so"
        )

        shutil.copy2(
            libpython[0],
            momo_dir / "lib/arm64-v8a/libpython3.14.so"
        )


    stdlib = prefix / "lib/python3.14"

    shutil.copytree(
        stdlib,
        momo_dir / "assets/python/lib/python3.14",
        dirs_exist_ok=True
    )

    main_py = momo_dir / "assets/python/scripts/main.py"

    main_py.write_text(
        'print("YOOOOOOOOOOO")'
    )


    # FOR legacy purpose i create this, but maybe remove?? #TODO
    strings = momo_dir / "res/values/strings.xml"

    strings.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Momo App</string>
</resources>
        """
    )


    print("Momo initialized successfully.")


else:
    print("Momo already initialized.")
