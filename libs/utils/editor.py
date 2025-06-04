import json
import os
import subprocess
import sys
import tempfile
from typing import List, Optional, Union

from _pkgmanager import find_executable, require_package
from _shutil import start_process


def edit_file(file: str, start_insert=False):
    args = ["nvim", file]
    if start_insert:
        args.append("+startinsert")
    subprocess.call(args)


def edit_text(text: str, tmp_file_ext=".txt"):
    with tempfile.NamedTemporaryFile(
        suffix=tmp_file_ext, mode="w+", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_file.write(text)
        tmp_filename = tmp_file.name

    edit_file(tmp_filename)

    with open(tmp_filename, "r", encoding="utf-8") as f:
        new_text = f.read().rstrip("\n")
    return new_text


def vscode_set_include_path(include_path):
    include_path = [os.path.abspath(x).replace("\\", "/") for x in include_path]
    include_path.insert(0, "${workspaceFolder}/**")

    # Default configuration file
    data = {"configurations": [{"name": "Win32", "includePath": []}]}

    c_cpp_properties = ".vscode/c_cpp_properties.json"
    if os.path.exists(c_cpp_properties):
        with open(c_cpp_properties) as f:
            data = json.load(f)

    data["configurations"][0]["includePath"] = include_path

    os.makedirs(".vscode", exist_ok=True)
    with open(c_cpp_properties, "w") as f:
        json.dump(data, f, indent=4)


def is_vscode_available() -> bool:
    # If a graphical display is not available in a Linux environment, return false.
    if sys.platform == "linux" and not os.environ.get("DISPLAY"):
        return False
    return find_executable("vscode") is not None


def open_in_vscode(
    file: Union[str, List[str]],
    line_number: Optional[int] = None,
    vscode_executable: Optional[str] = None,
):
    if vscode_executable:
        vscode = vscode_executable
    else:
        vscode = find_executable("vscode")
        if vscode is None:
            raise FileNotFoundError(
                "Cannot locate vscode executable, maybe not installed."
            )

    if isinstance(file, str):
        if line_number is None:
            args = [vscode, file]
        else:
            args = [vscode, "-g", "{}:{}".format(file, line_number)]
    else:
        args = [vscode] + file

    start_process(args)


def open_in_vim(file: str, line_number: Optional[int] = None):
    require_package("neovim")
    args = ["nvim"]
    if line_number is not None:
        args.append(f"+{line_number}")
    args.append(file)
    subprocess.call(args)


def open_code_editor(path: Union[str, List[str]], line_number: Optional[int] = None):
    if is_vscode_available():
        open_in_vscode(path, line_number=line_number)
    else:
        open_in_vim(
            file=path if (isinstance(path, str)) else path[-1], line_number=line_number
        )
