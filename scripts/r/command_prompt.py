import subprocess
import sys

from _android import setup_android_env
from _cmake import setup_cmake
from _shutil import cd_current_dir, print2, setup_logger, setup_nodejs

if __name__ == "__main__":
    setup_logger()

    try:
        setup_android_env()
    except Exception as ex:
        print2("WARN: %s" % ex)

    cd_current_dir()

    setup_cmake(install=False)

    setup_nodejs(install=False)

    if sys.platform == "win32":
        subprocess.call(["cmd"])
    else:
        subprocess.call(["bash"])
