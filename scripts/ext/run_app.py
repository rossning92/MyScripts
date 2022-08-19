import subprocess
import sys

from _pkgmanager import get_executable

if __name__ == "__main__":
    app = sys.argv[1]
    args = sys.argv[2:]
    ret = subprocess.call([get_executable(app), *args])
    sys.exit(ret)
