#!/usr/bin/env python

import argparse
import os
import sys

from _shutil import start_process


def open_new(url):
    CHROME_PATH = [
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "C:\Program Files\Chrome\Application\chrome.exe",
    ]

    if sys.platform == "win32":
        for path in CHROME_PATH:
            if os.path.isfile(path):
                start_process(
                    [
                        path,
                        r"--user-data-dir=%s"
                        % os.path.abspath("/tmp/chrome-dev-user-profile"),
                        # "--new-window",
                        url,
                    ]
                )
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", type=str)
    args = parser.parse_args()

    open_new(args.url)
