import subprocess
import os
import pathlib


def open_page(url):
    subprocess.call(
        [
            "C:\Program Files (x86)\Chromium\Application\chrome.exe",
            "--user-data-dir=%s"
            % os.path.join(pathlib.Path.home(), "ChromeDataForDev"),
            url,
        ]
    )
