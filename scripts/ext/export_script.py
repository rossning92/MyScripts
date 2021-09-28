import os
import re
import shutil
import time

from _script import get_python_path


exported_python_modules = set()
exported_scripts = set()


def find_module(python_path, module):
    for p in python_path:
        path = os.path.join(p, module + ".py")
        if os.path.exists(path):
            return path
    return None


def export_python(script_path):
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

        if python_module not in exported_python_modules:
            exported_python_modules.add(python_module)

            print("Copy: %s" % python_module)
            shutil.copy(python_module, OUT_DIR)

            # Find dependencies recursively
            export_python(python_module)


def export_script(script_path):
    with open(script_path, "r") as f:
        content = f.read()

    # Find dependencies to other scripts
    old_new_path_map = {}
    other_scripts = re.findall(
        r"(?<=\W)(?:(?:\w+|\.\.)/)*\w+\.(?:py|cmd|ahk|sh)(?=\W)", content
    )
    print(other_scripts)
    for s in other_scripts:
        script_abs_path = os.path.abspath(os.path.dirname(script_path) + "/" + s)

        if script_abs_path not in exported_scripts:
            exported_scripts.add(script_abs_path)
            file_name = os.path.basename(script_abs_path)
            if os.path.exists(script_abs_path):
                shutil.copy(script_abs_path, "%s/%s" % (OUT_DIR, file_name))
                old_new_path_map[s] = file_name
                print("Copy: %s" % script_abs_path)
                export_script(script_abs_path)  # Recurse

    if os.path.splitext(script_path)[1] == ".py":
        export_python(script_path)

        launcher = f"{OUT_DIR}{os.path.sep}{os.path.splitext(os.path.basename(script_path))[0]}.cmd"
        shutil.copy(
            "../../install/find_python.cmd", f"{OUT_DIR}{os.path.sep}_find_python.cmd"
        )
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
    out_file = "%s/%s" % (OUT_DIR, os.path.basename(script_path))
    print("Render: %s" % script_path)
    with open(out_file, "w") as f:
        f.write(content)


if __name__ == "__main__":
    OUT_DIR = os.path.abspath(os.path.expanduser("~/Desktop/script_export"))
    if os.path.isdir(OUT_DIR):
        shutil.rmtree(OUT_DIR)
        time.sleep(1)
    os.makedirs(OUT_DIR, exist_ok=True)

    script_path = os.getenv("_SCRIPT")

    export_script(script_path)
