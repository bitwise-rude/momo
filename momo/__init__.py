from . import build
import pathlib
import shutil

class App:
    PROJECT_ROOT = pathlib.Path(".momo")
    def __init__(self, source_path:str) -> None:
        self.source_path = source_path
        dest_path = App.PROJECT_ROOT / 'assets' / 'python' / 'scripts' / 'main.py'
        shutil.copy(source_path,dest_path)

    def build(self):
        # Check if we need to quick_rebuild or compile native lib or just bulild: 
        if not (App.PROJECT_ROOT / 'lib' / 'arm64-v8a' / 'libnative-lib.so').exists():
            build.compile_python()
            build.build_python()
        elif (App.PROJECT_ROOT / 'build' / 'app-base.apk').exists():
            print("QUICK REBUILDING..")
            build.quick_rebuild()
