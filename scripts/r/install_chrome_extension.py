import os
import subprocess
import sys

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))

if __name__ == "__main__":
    if sys.platform == "win32":
        subprocess.call(["taskkill", "/f", "/im", "chrome.exe"])
    print(os.path.join(SCRIPT_ROOT, "hello_chrome_extension"))
    subprocess.check_call(
        [
            "chrome",
            "--load-extension=%s" % os.path.join(SCRIPT_ROOT, "hello_chrome_extension"),
        ]
    )
