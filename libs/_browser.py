import os
import subprocess
import sys
import tempfile
import webbrowser

from _shutil import is_in_termux
from utils.process import start_process


def open_url(url, profile_name=None):
    if sys.platform == "win32":
        CHROME_PATH = [
            r"C:\Program Files\Chrome\Application\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]

        for chrome_executable in CHROME_PATH:
            if os.path.isfile(chrome_executable):
                args = [chrome_executable]
                if profile_name:
                    profile_dir = os.path.join(
                        tempfile.gettempdir(), "ChromeDevProfile"
                    )
                    os.makedirs(profile_dir, exist_ok=True)
                    args.append("--user-data-dir=%s" % profile_dir)
                args.append(url)
                start_process(args)
                return
    elif is_in_termux():
        subprocess.call(["termux-open-url", url])
    else:
        webbrowser.open(url)
