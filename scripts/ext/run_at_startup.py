import os
import sys

from _shutil import call_echo

if __name__ == "__main__":
    if sys.platform == "win32":
        path = os.path.realpath("../../run.cmd")

        call_echo(
            [
                "reg",
                "add",
                "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run",
                "/v",
                "MyScripts",
                "/t",
                "REG_SZ",
                "/d",
                '"' + path + '"',
                "/f",
            ]
        )
