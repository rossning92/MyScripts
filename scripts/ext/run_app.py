import subprocess
import sys

from _pkgmanager import require_package

if __name__ == "__main__":
    app = sys.argv[1]
    args = sys.argv[2:]
    ret = subprocess.call([require_package(app), *args])
    sys.exit(ret)
