import re
import sys

from _android import setup_android_env
from _shutil import check_output

if __name__ == "__main__":
    setup_android_env()
    out = check_output(["aapt", "dump", "badging", sys.argv[-1]])
    pkg_name = re.findall("name='([\w.]+)", out)[0]
    print(pkg_name)
