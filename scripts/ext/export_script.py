import os
import re
import shutil

from _editor import open_code_editor
from _script import get_python_path, render_script

_exported_python_modules = set()
_exported_scripts = set()


def find_module(python_path, module):
    for p in python_path:
        path = os.path.join(p, module + ".py")
        if os.path.exists(path):
            return path
    return None


def _export_python_module_recursive(script_path, out_dir):
    with open(script_path, "rb") as f:
        content = f.read()

    # Find imports dependencies
    module_names = re.findall(
        rb"(?:^from|import) (_[a-zA-Z0-9_]+)", content, flags=re.MULTILINE
    )

    search_paths = get_python_path(script_path)
    for m in module_names:
        m = m.decode()
        python_module = find_module(search_paths, m)
        if python_module is None:
            raise Exception("Cannot find python module: %s" % m)

        if python_module not in _exported_python_modules:
            _exported_python_modules.add(python_module)

            print("Copy: %s" % python_module)
            shutil.copy(python_module, out_dir)

            # Find dependencies recursively
            _export_python_module_recursive(python_module, out_dir)


def _export_script(script_path, out_dir, create_executable=False):
    ext = os.path.splitext(script_path)[1]
    script_name = os.path.splitext(os.path.basename(script_path))[0]

    content = ""
    if ext == ".sh":
        content += (
            "export MSYS_NO_PATHCONV=1\n"
            "export CHERE_INVOKING=1\n"
            "export MSYSTEM=MINGW64\n"
            "export MSYS2_PATH_TYPE=inherit\n"
        )

    content += render_script(script_path)

    # Find dependencies to other scripts
    old_new_path_map = {}
    other_scripts = re.findall(
        r"(?<=\W)(?:(?:\w+|\.\.)/)*\w+\.(?:py|cmd|ahk|sh)(?=\W)", content
    )
    print(other_scripts)
    for s in other_scripts:
        script_abs_path = os.path.abspath(os.path.dirname(script_path) + "/" + s)

        if script_abs_path not in _exported_scripts:
            _exported_scripts.add(script_abs_path)
            file_name = os.path.basename(script_abs_path)
            if os.path.exists(script_abs_path):
                shutil.copy(script_abs_path, "%s/%s" % (out_dir, file_name))
                old_new_path_map[s] = file_name
                print("Copy: %s" % script_abs_path)
                _export_script(script_abs_path, out_dir)  # Recurse

    if ext == ".py":
        _export_python_module_recursive(script_path, out_dir)

        launcher = f"{out_dir}{os.path.sep}{os.path.splitext(os.path.basename(script_path))[0]}.cmd"
        # shutil.copy(
        #     "../../install/find_python.cmd", f"{out_dir}{os.path.sep}_find_python.cmd"
        # )
        with open(launcher, "w") as f:
            f.write(
                "@echo off\n"
                + 'cd /d "%~dp0"\n'
                + "call _find_python.cmd\n"
                + "if exist requirements.txt pip install -r requirements.txt\n"
                + "python %s\n" % os.path.basename(script_path)
                + "if %errorlevel% neq 0 pause\n"
            )

    # Replace script path
    for k, v in old_new_path_map.items():
        content = content.replace(k, v)

    # Render scripts
    out_file = "%s/%s" % (out_dir, os.path.basename(script_path))
    print("Render: %s" % script_path)
    with open(out_file, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    if create_executable and ext == ".py":
        os.rename(
            os.path.join(out_dir, script_name + ".py"),
            os.path.join(out_dir, "__main__.py"),
        )
        shutil.make_archive(os.path.join(out_dir, script_name), "zip", out_dir)
        out_executable = os.path.join(out_dir, script_name) + ".pyz"
        os.rename(
            os.path.join(out_dir, script_name) + ".zip",
            out_executable,
        )
        return out_executable
    else:
        return out_file


def export_script(script_path, out_dir, create_executable=False):
    if os.path.isdir(out_dir):
        shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir, exist_ok=True)
    return _export_script(script_path, out_dir, create_executable)


if __name__ == "__main__":
    out_dir = os.path.abspath(os.path.expanduser("~/Desktop/script_export"))
    script_path = os.getenv("SCRIPT")

    out_file = export_script(script_path, out_dir, create_executable=True)
    open_code_editor(out_file)
    # shell_open(out_dir)
