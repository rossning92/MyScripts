import os
import subprocess

from _shutil import start_process
from config_vscode import config_vscode, get_vscode_cmdline


def open_vscode(data_dir):
    subprocess.Popen(get_vscode_cmdline(data_dir=data_dir), shell=True, close_fds=True)


if __name__ == "__main__":
    os.environ["PATH"] = (
        os.environ["PATH"] + os.pathsep + r"C:\Program Files\Microsoft VS Code"
    )

    data_dir = os.path.expanduser("~/VSCodeCompactUserData")
    config_vscode(data_dir=data_dir, compact=True)
    start_process(
        [
            "code",
            "--user-data-dir",
            data_dir,
        ]
    )
    open_vscode(data_dir=data_dir)
