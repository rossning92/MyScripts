import logging
import subprocess
import sys

from _cpp import setup_cmake
from _shutil import setup_logger, setup_nodejs

if __name__ == "__main__":
    setup_logger(level=logging.INFO)

    setup_cmake(install=False)

    setup_nodejs(install=False)

    if sys.platform == "win32":
        subprocess.call(["cmd", "/k", "echo."])
    else:
        subprocess.call(["bash"])
