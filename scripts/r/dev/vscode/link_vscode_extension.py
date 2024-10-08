import argparse
import os
import subprocess
import sys


def link_vscode_extension(extension_dir: str):
    if not os.path.exists(extension_dir):
        raise Exception(f"VSCode extension path does not exist: {extension_dir}")

    extension_name = os.path.basename(extension_dir)

    if sys.platform == "win32":
        if not os.path.exists(extension_dir):
            raise Exception(f"VSCode extension path does not exist: {extension_dir}")
        subprocess.call(
            f'MKLINK /J "%USERPROFILE%\\.vscode\\extensions\\{extension_name}" "{extension_dir}"',
            shell=True,
        )
    elif sys.platform == "linux":
        subprocess.call(
            [
                "ln",
                "-s",
                extension_dir,
                os.path.expanduser("~/.vscode/extensions/{extension_name}"),
            ],
        )
    else:
        raise Exception("Unsupported platform: " + sys.platform)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process extension directory.")
    parser.add_argument(
        "extension_dir", type=str, help="Directory of the VSCode extension"
    )
    args = parser.parse_args()

    link_vscode_extension(args.extension_dir)
