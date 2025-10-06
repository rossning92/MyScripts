import argparse
import logging
import os
import sys

from utils.symlink import create_symlink


def link_vscode_extension(extension_dir: str):
    if not os.path.exists(extension_dir):
        raise Exception(f"VSCode extension path does not exist: {extension_dir}")

    package_file = os.path.join(extension_dir, "package.json")
    if not os.path.exists(package_file):
        raise Exception(
            f"Invalid extension path because the file does not exist: {package_file}"
        )

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
        symlink_path = os.path.expanduser(f"~/.vscode/extensions/{extension_name}")
    else:
        raise Exception("Unsupported platform: " + sys.platform)

    logging.debug(f"Create symbolic link: {args}")
    os.makedirs(os.path.dirname(symlink_path), exist_ok=True)
    create_symlink(extension_dir, symlink_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process extension directory.")
    parser.add_argument(
        "extension_dir", type=str, help="Directory of the VSCode extension"
    )
    args = parser.parse_args()

    link_vscode_extension(args.extension_dir)
