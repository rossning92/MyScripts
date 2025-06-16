import os
import pathlib
import sys

from utils.create_symlink import create_symlink


def _main():
    # nvim config dir
    nvim_config = str(
        pathlib.Path(__file__).resolve().parent.parent.parent / "settings" / "nvim"
    )

    # symlink path
    if sys.platform in ("linux", "darwin"):
        # Create the .config dir if it does not exist
        config_path = pathlib.Path.home() / ".config"
        config_path.mkdir(parents=True, exist_ok=True)

        symlink_path = str(config_path / "nvim")
    elif sys.platform == "win32":
        symlink_path = os.path.expandvars("%LOCALAPPDATA%\\nvim")

    create_symlink(nvim_config, symlink_path)


if __name__ == "__main__":
    _main()
