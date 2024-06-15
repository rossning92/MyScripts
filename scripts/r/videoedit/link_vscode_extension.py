import os
import subprocess
import sys


def link_vscode_extension():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    extension_path = os.path.join(script_dir, "_extension")

    if sys.platform == "win32":
        if not os.path.exists(extension_path):
            raise Exception(f"VSCode extension path does not exist: {extension_path}")
        subprocess.call(
            f'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\videoedit" "{extension_path}"',
            shell=True,
        )
    elif sys.platform == "linux":
        subprocess.call(
            [
                "ln",
                "-s",
                extension_path,
                os.path.expanduser("~/.vscode/extensions/videoedit"),
            ],
        )
    else:
        raise Exception("Unsupported platform: " + sys.platform)


if __name__ == "__main__":
    link_vscode_extension()
