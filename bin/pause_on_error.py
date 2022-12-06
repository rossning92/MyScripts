import subprocess
import sys

ret = subprocess.call(sys.argv[1:])
if ret != 0:
    print("---")
    print("(press enter to exit...)")
    input()
