from _shutil import *
from _editor import *

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
    "screenshot",
    "tmp",
    "video",
]:
    os.makedirs(os.path.join(proj_dir, d), exist_ok=True)


# HACK:
prepend_to_path(os.path.expandvars("%LOCALAPPDATA%\\ocenaudio"))

jsconfig = os.path.join(proj_dir, "jsconfig.json")
if not os.path.exists(""):
    with open(jsconfig, "w") as f:
        json.dump(
            {
                "compilerOptions": {
                    "module": "commonjs",
                    "target": "es2016",
                    "jsx": "preserve",
                    "baseUrl": os.path.abspath("movy/src").replace("\\", "/"),
                },
                "exclude": ["node_modules", "**/node_modules/*"],
            },
            f,
            indent=4,
        )


open_in_vscode([proj_dir, os.path.join(proj_dir, "index.md")])
