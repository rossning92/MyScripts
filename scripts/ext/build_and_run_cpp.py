import subprocess
import sys

from _cpp import compile

if __name__ == "__main__":
    out = compile(sys.argv[1])
    subprocess.check_call([out])
