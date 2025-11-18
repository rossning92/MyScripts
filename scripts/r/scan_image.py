import os
import subprocess
import sys

from _shutil import get_home_path, get_time_str
from utils.process import start_process

if __name__ == "__main__":
    out_file = os.path.join(get_home_path(), "Desktop", f"scan_{get_time_str()}.jpg")

    if sys.platform == "linux":
        subprocess.check_call(["run_script", "r/linux/scan_to_image.sh", out_file])
    elif sys.platform == "win32":
        subprocess.check_call(["run_script", "r/win/scan_to_image.ps1", out_file])
    else:
        raise Exception("Unsupported OS.")

    subprocess.check_call(
        ["run_script", "r/image/auto_crop_image.py", out_file, "--inplace"]
    )
    # subprocess.check_call(["run_script", "r/image/to_grayscale.sh", out_file])
    # shell_open(out_file)
    start_process(["nsxiv", out_file])
