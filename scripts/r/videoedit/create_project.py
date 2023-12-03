import json
import os
import subprocess

from _editor import open_code_editor
from _shutil import prepend_to_path

proj_dir = r"{{VIDEO_PROJECT_DIR}}"

if not proj_dir:
    raise Exception("Invalid project dir.")

subprocess.call(
    'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\videoedit" "{}"'.format(
        os.path.join(os.getcwd(), "_extension")
    ),
    shell=True,
)


for d in [
    "animation",
    "image",
    "overlay",
    "record",
    "screencap",
    "video",
]:
    os.makedirs(os.path.join(proj_dir, d), exist_ok=True)

# HACK:
prepend_to_path(os.path.expandvars("%LOCALAPPDATA%\\ocenaudio"))

jsconfig = os.path.join(proj_dir, "animation", "jsconfig.json")
if not os.path.exists(jsconfig):
    with open(jsconfig, "w") as f:
        json.dump(
            {
                "compilerOptions": {
                    "module": "commonjs",
                    "target": "es2016",
                    "jsx": "preserve",
                    "baseUrl": os.getcwd().replace("\\", "/"),
                },
                "exclude": ["node_modules", "**/node_modules/*"],
            },
            f,
            indent=4,
        )


open_code_editor([proj_dir, os.path.join(proj_dir, "index.md")])
