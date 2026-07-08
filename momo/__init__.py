# Momo - written by Meyan Adhikari

import inspect
from pathlib import Path
import shutil

caller_frame = inspect.stack()[1]
caller_path = Path(caller_frame.filename).resolve()
caller_dir = caller_path.parent

# Main directory consisting of project files in the user's project
momo_dir = Path(caller_dir / ".momo")
module_dir = Path(__file__).resolve().parent

if not momo_dir.is_dir():
    
    # Files needed to be copied
    source_xml = module_dir / "AndroidManifest.xml"  
    source_java = module_dir / "MainActivity.java"
    source_c = module_dir / "glue.c"

    print("Initialized a directory .momo in the project folder. Do not modify it.")
    momo_dir.mkdir(parents=True, exist_ok=True)

    subfolders = ["build", "src"]
    for folder in subfolders:
        (momo_dir / folder).mkdir(parents=True, exist_ok=True)
    
    destination_xml = momo_dir / source_xml.name
    shutil.copy2(source_xml, destination_xml)
    destination_java = momo_dir / "src"/ source_java.name
    shutil.copy2(source_c, destination_java)
    destination_c = momo_dir / "src"/ source_c.name
    shutil.copy2(source_c, destination_c)

else:
    print("Momo is already initialized in your project folder. Please do not modify or delete the .momo folder in this directory.")
