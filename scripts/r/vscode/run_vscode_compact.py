import os

from _shutil import start_process

from config_vscode import config_vscode

os.environ["PATH"] = (
    os.environ["PATH"] + os.pathsep + r"C:\Program Files\Microsoft VS Code"
)

config_vscode(data_dir=os.path.expanduser("~/VSCodeTempUserData"), compact=True)
start_process(
    [
        "code",
        "--user-data-dir",
        os.path.expanduser("~/VSCodeTempUserData"),
    ]
)
