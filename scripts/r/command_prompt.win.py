import logging
import subprocess
import sys

from _android import setup_android_env
from _cpp import setup_cmake
from _shutil import setup_nodejs
from utils.logger import setup_logger

if __name__ == "__main__":
    setup_logger(level=logging.INFO)
    setup_cmake(install=False)
    setup_nodejs(install=False)

    try:
        setup_android_env()
    except Exception as ex:
        print(f"WARN: {ex}")

    if sys.platform == "win32":
        subprocess.call(["cmd", "/k", "echo."])
    else:
        subprocess.call(["bash"])
