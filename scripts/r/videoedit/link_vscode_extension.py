import os
import subprocess
import sys

if __name__ == "__main__":
    if sys.platform == "win32":
        subprocess.call(
            'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\videoedit" "{}"'.format(
                os.path.join(os.getcwd(), "_extension")
            ),
            shell=True,
        )
