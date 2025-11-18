import os
import subprocess
import sys

from utils.process import start_process

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]
    script_dir = os.path.dirname(script_path)
    os.chdir(script_dir)
    print("Open Folder: " + os.getcwd())

    if sys.platform == "darwin":
        subprocess.call("open .", shell=True)
    elif sys.platform == "win32":
        subprocess.call(["cmd", "/c", "start", "", os.getcwd()])
    elif sys.platform == "linux":
        start_process(["xdg-open", "."])
