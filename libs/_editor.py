import glob
import json
import os
import subprocess

from _pkgmanager import find_executable, require_package
from _shutil import exec_ahk, start_process


def get_pycharm_executable():
    files = glob.glob(
        r"C:\Program Files\JetBrains\**\pycharm64.exe", recursive=True
    ) + glob.glob(r"C:\Program Files (x86)\JetBrains\**\pycharm64.exe", recursive=True)
    if len(files) == 0:
        raise Exception("Cannot find pycharm.")
    pycharm = files[0]
    return pycharm


def open_in_pycharm(path):
    pycharm = get_pycharm_executable()
    subprocess.Popen([pycharm, path])

    ahk_script = os.path.join(os.path.dirname(__file__), "_activate_pycharm.ahk")
    subprocess.Popen(["AutoHotkeyU64.exe", ahk_script])


def open_in_androidstudio(path, line=None):
    args = [r"C:\Program Files\Android\Android Studio\bin\studio64.exe"]
    if line is not None:
        args += ["--line", str(line)]
    args.append(path)
    subprocess.Popen(args)
    exec_ahk("WinActivate ahk_exe studio64.exe")


def vscode_set_include_path(include_path):
    include_path = [os.path.abspath(x).replace("\\", "/") for x in include_path]
    include_path.insert(0, "${workspaceFolder}/**")

    # Default configuration file
    data = {"configurations": [{"name": "Win32", "includePath": []}]}

    F = ".vscode/c_cpp_properties.json"
    if os.path.exists(F):
        with open(F) as f:
            data = json.load(f)

    data["configurations"][0]["includePath"] = include_path

    os.makedirs(".vscode", exist_ok=True)
    with open(F, "w") as f:
        json.dump(data, f, indent=4)


def open_in_vscode(file, line_number=None, vscode_executable=None):
    if vscode_executable:
        vscode = vscode_executable
    else:
        require_package("vscode")
        vscode = find_executable("vscode")
        if vscode is None:
            raise FileNotFoundError(
                "Cannot locate vscode executable, maybe not installed."
            )

    if type(file) == str:
        if line_number is None:
            args = [vscode, file]
        else:
            args = [vscode, "-g", "{}:{}".format(file, line_number)]
    else:
        args = [vscode] + file

    start_process(args)


def open_in_vim(file, line_number=None):
    subprocess.call(["vi", file])


def open_in_editor(path, line_number=None):
    try:
        open_in_vscode(path, line_number=line_number)
    except FileNotFoundError:
        open_in_vim(path if (type(path) == str) else path[-1], line_number=line_number)
    except FileNotFoundError:
        raise
