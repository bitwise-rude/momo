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

    print("Initialized a directory .momo in the project folder. Do not modify it.")
    momo_dir.mkdir(parents=True, exist_ok=True)

    subfolders = ["build", "src"]
    for folder in subfolders:
        (momo_dir / folder).mkdir(parents=True, exist_ok=True)

    if source_xml.exists():
        destination_xml = momo_dir / source_xml.name
        shutil.copy2(source_xml, destination_xml)
    else:
        print(f"SOME ERROR OCCURED IN THE INSTALLATION OF MOMO")
else:
    print("Momo is already initialized in your project folder. Please do not modify or delete the .momo folder in this directory.")
