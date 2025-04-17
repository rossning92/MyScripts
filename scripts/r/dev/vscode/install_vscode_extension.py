import argparse
import logging
import os
import sys

from utils.create_symlink import create_symlink


def link_vscode_extension(extension_dir: str):
    if not os.path.exists(extension_dir):
        raise Exception(f"VSCode extension path does not exist: {extension_dir}")

    extension_name = os.path.basename(extension_dir)

    if not os.path.isabs(extension_dir):
        extension_dir = os.path.abspath(extension_dir)

    if not os.path.isdir(extension_dir):
        raise Exception(f"{extension_dir} must be a valid dir")

    if not os.path.exists(extension_dir):
        raise Exception(f"VSCode extension path does not exist: {extension_dir}")
    if sys.platform == "win32":
        symlink_path = os.path.expandvars(
            f"%USERPROFILE%\\.vscode\\extensions\\{extension_name}"
        )
    elif sys.platform == "linux":
        symlink_path = os.path.expanduser("~/.vscode/extensions/{extension_name}")
    else:
        raise Exception("Unsupported platform: " + sys.platform)

    logging.debug(f"Create symbolic link: {args}")
    create_symlink(extension_dir, symlink_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process extension directory.")
    parser.add_argument(
        "extension_dir", type=str, help="Directory of the VSCode extension"
    )
    args = parser.parse_args()

    link_vscode_extension(args.extension_dir)
