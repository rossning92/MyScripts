from _shutil import *
from _editor import *

subprocess.call(
    'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\my-animation-extension" "{}"'.format(
        os.path.join(os.getcwd(), "_extension")
    ),
    shell=True,
)

open_in_vscode(r"{{VIDEO_PROJECT_DIR}}")
