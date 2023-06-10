import json
import logging
import os
import re
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple

from _editor import open_in_editor
from _script import (
    Script,
    get_absolute_script_path,
    get_all_scripts,
    get_data_dir,
    get_my_script_root,
    get_relative_script_path,
    get_script_config_file,
    get_script_config_file_path,
    get_script_default_config,
    get_script_directories,
    get_script_root,
)
from _shutil import load_yaml, quote_arg, save_yaml, set_clip
from _template import render_template_file
from _term import DictEditWindow, Menu

SCRIPT_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_selected_script_path_rel(script_path=None):
    if script_path is None:
        script_path = os.getenv("SCRIPT")
        assert script_path
    rel_path = script_path.replace(get_script_root() + os.path.sep, "")
    rel_path = rel_path.replace("\\", "/")
    return rel_path


def get_selected_script_dir_rel(script_path=None):
    rel_path = get_selected_script_path_rel(script_path=script_path)
    rel_path = os.path.dirname(rel_path)
    if rel_path:
        rel_path += "/"
    return rel_path


def edit_myscript_script(file):
    if os.path.splitext(file)[1] == ".link":
        file = open(file, "r", encoding="utf-8").read().strip()

    project_folder = os.path.abspath(os.path.join(SCRIPT_ROOT, ".."))
    if file.startswith(project_folder):
        open_in_editor([project_folder, file])
        return

    script_dirs = get_script_directories()
    for _, d in script_dirs:
        if d in file:
            open_in_editor([d, file])
            return

    open_in_editor([file])


def enter_script_path():
    script_dir = get_selected_script_dir_rel().lstrip("/")
    script_path = input("Script path (%s [Enter]): " % script_dir)
    if not script_path:
        script_name = input("Script path %s" % script_dir)
        if not script_name:
            return ""

        script_path = script_dir + script_name

    # Check if new script should be saved in script directories
    script_dirs = get_script_directories()
    arr = script_path.split("/")
    if arr:
        matched_script_dir = next(filter(lambda x: x[0] == arr[0], script_dirs), None)
        if matched_script_dir:
            arr[0] = matched_script_dir[1]
    script_path = "/".join(arr)

    return script_path


def edit_script_config(script_path):
    default_config = get_script_default_config()

    script_config_file = get_script_config_file_path(script_path)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    def on_dict_update(dict):
        data = {k: v for k, v in dict.items() if default_config[k] != v}
        save_yaml(data, script_config_file)

    config_edit_history_file = os.path.join(get_data_dir(), "config_edit_history.json")
    if os.path.exists(config_edit_history_file):
        with open(config_edit_history_file, "r") as f:
            config_edit_history = json.load(f)
    else:
        config_edit_history = {}

    def on_dict_history_update(config_edit_history: Dict[str, List[Any]]):
        with open(config_edit_history_file, "w", encoding="utf-8") as f:
            json.dump(config_edit_history, f, indent=2)

    script_config_file_rel_path = get_relative_script_path(script_config_file)
    w = DictEditWindow(
        data,
        default_dict=default_config,
        on_dict_update=on_dict_update,
        label=f"edit {script_config_file_rel_path}",
        on_dict_history_update=on_dict_history_update,
        dict_history=config_edit_history,
    )
    ret = w.exec()
    if ret == -1:
        return False
    else:
        return True


def copy_script_path_to_clipboard(
    script: Script, with_variables=False, format="cmdline"
):
    script_path = script.script_path
    _, ext = os.path.splitext(script_path)
    if ext == ".md" or ext == ".txt":
        with open(script_path, "r", encoding="utf-8") as f:
            set_clip(f.read())
        logging.info("Content is copied to clipboard.")
    else:
        # Convert to relative path
        script_path = get_relative_script_path(script_path)
        if " " in script_path:  # quote  path if it contains spaces
            script_path = '"' + script_path + '"'

        if format == "cmdline":
            content = ""
            if with_variables:
                for k, v in script.get_variables().items():
                    if v:
                        content += "%s=%s " % (k, quote_arg(v, shell_type="bash"))

            content += f"run_script {script_path}"
        elif format == "include":
            if with_variables:
                content = "{{ include('%s', %s) }}" % (
                    script_path,
                    script.get_variables(),
                )
            else:
                content = "{{ include('%s') }}" % script_path

        set_clip(content)
        return content


def create_new_script(ref_script_path=None, duplicate=False):
    label: str
    if duplicate:
        text = get_selected_script_path_rel(script_path=ref_script_path)
        label = "duplicate script"
    else:
        text = get_selected_script_dir_rel(script_path=ref_script_path)
        label = "new script"
    w: Menu = Menu(label=label, text=text)
    w.exec()
    dest_script = w.get_text()
    if not dest_script:
        return

    # Convert to abspath
    dest_script = get_absolute_script_path(dest_script)
    dest_script_config_file = get_script_config_file_path(dest_script)

    dir_name = os.path.dirname(dest_script)
    if dir_name != "":
        os.makedirs(dir_name, exist_ok=True)

    # Check script extensions
    _, ext = os.path.splitext(dest_script)
    if not ext:
        logging.warning("Script extension is required.")

    if duplicate:
        if not os.path.isabs(ref_script_path):
            src_script = os.path.join(get_script_root(), ref_script_path)
        else:
            src_script = ref_script_path
        shutil.copyfile(src_script, dest_script)
        src_script_config_file = get_script_config_file(src_script)
        if src_script_config_file:
            shutil.copyfile(src_script_config_file, dest_script_config_file)

    else:
        template_root = os.path.join(get_my_script_root(), "templates")
        if ext == ".py":
            shutil.copyfile(os.path.join(template_root, "python.py"), dest_script)
        elif ext == ".mmd":
            shutil.copyfile(os.path.join(template_root, "mermaid.mmd"), dest_script)
        elif dest_script.endswith(".user.js"):
            userscript_name = re.sub(r"\.user\.js$", "", os.path.basename(dest_script))
            render_template_file(
                os.path.join(get_my_script_root(), "templates", "userscript.user.js"),
                dest_script,
                context={
                    "USERSCRIPT_NAME": userscript_name,
                    "USERSCRIPT_LIB": "http://127.0.0.1:4312/userscriptlib.js",
                },
            )
        else:
            # Create empty file
            with open(dest_script, "w") as _:
                pass

    edit_myscript_script(os.path.realpath(dest_script))
    return dest_script


def replace_script_str(
    old,
    new=None,
    dry_run=False,
    matched_files: Optional[List[str]] = None,
    on_progress: Optional[Callable[[str], None]] = None,
) -> List[Tuple[str, int, str]]:
    modified_lines: List[Tuple[str, int, str]] = []

    if not dry_run and matched_files is not None:
        files = matched_files
    else:
        files = list(get_all_scripts())

    for i, file in enumerate(files):
        if on_progress is not None:
            if i % 20 == 0:
                on_progress("searching (%d/%d)" % (i + 1, len(files)))

        with open(file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        dirty = False
        for i, line in enumerate(lines):
            if old in line:
                if dry_run:
                    modified_lines.append(
                        (get_relative_script_path(file), i + 1, lines[i])
                    )
                else:
                    lines[i] = line.replace(old, new)
                dirty = True

        if dirty:
            if matched_files is not None:
                matched_files.append(file)
            if not dry_run:
                s = "\n".join(lines)
                with open(file, "w", encoding="utf-8") as f:
                    f.write(s)

    return modified_lines


def rename_script(
    script_full_path,
    on_progress: Optional[Callable[[str], None]] = None,
):
    script_rel_path = get_relative_script_path(script_full_path)
    matched_files: List[str] = []
    modified_lines = replace_script_str(
        script_rel_path,
        dry_run=True,
        matched_files=matched_files,
        on_progress=on_progress,
    )

    items = [f"{x[0]}:{x[1]}:\t{x[2]}" for x in modified_lines]
    w = Menu(label="new name", text=script_rel_path, items=items)
    w.exec()
    new_script_rel_path = w.get_text()
    if not new_script_rel_path:
        return False

    # Rename script
    new_script_full_path = get_absolute_script_path(new_script_rel_path)
    os.makedirs(os.path.dirname(new_script_full_path), exist_ok=True)
    os.rename(script_full_path, new_script_full_path)

    # Rename config file if any
    config_file = get_script_config_file_path(script_full_path)
    new_config_file = get_script_config_file_path(new_script_full_path)
    if os.path.exists(config_file):
        os.rename(config_file, new_config_file)

    # Replace script string
    replace_script_str(
        script_rel_path, new_script_rel_path, matched_files=matched_files
    )
    return True
