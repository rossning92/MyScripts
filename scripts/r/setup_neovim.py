import os
import pathlib
import sys

from utils.symlink import create_symlink


def main():
    src = pathlib.Path(__file__).resolve().parents[2] / "settings" / "nvim"

    if sys.platform == "win32":
        dest = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "nvim"
    else:
        dest = pathlib.Path.home() / ".config" / "nvim"
        dest.parent.mkdir(parents=True, exist_ok=True)

    create_symlink(str(src), str(dest))


if __name__ == "__main__":
    main()
