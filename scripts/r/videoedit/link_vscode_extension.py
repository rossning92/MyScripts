import os
import subprocess
import sys

if __name__ == "__main__":
    if sys.platform == "win32":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        extension_path = os.path.join(script_dir, "_extension")
        if not os.path.exists(extension_path):
            raise Exception(f"extension path does not exists: {extension_path}")
        subprocess.call(
            f'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\videoedit" "{extension_path}"',
            shell=True,
        )
