import json
import logging
import os
import re
import shutil
from typing import Any, Callable, Dict, List, Optional, Tuple

from _editor import is_vscode_installed, open_code_editor, open_in_vscode
from _script import (
    Script,
    get_absolute_script_path,
    get_all_scripts,
    get_data_dir,
    get_default_script_config,
    get_my_script_root,
    get_relative_script_path,
    get_script_config_file,
    get_script_config_file_path,
    get_script_directories,
    get_script_root,
    save_json,
)
from _shutil import load_yaml, quote_arg, save_yaml
from _template import render_template_file
from utils.clip import set_clip
from utils.menu import Menu
from utils.menu.dictedit import DictEditMenu

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


def create_myscript_workspace() -> str:
    # Create a VSCode workspace to work with all scripts together.
    script_root = get_my_script_root()
    folders = [
        {
            "path": script_root,
        }
    ]
    folders.extend(
        [
            {"path": d.path}
            for d in get_script_directories()
            if script_root not in d.path
        ]
    )
    workspace_file = os.path.join(get_data_dir(), "myscripts.code-workspace")
    save_json(
        workspace_file,
        {
            "folders": folders,
        },
    )
    return workspace_file


def open_myscript_workspace():
    workspace_file = create_myscript_workspace()
    open_in_vscode([workspace_file])


def edit_myscript_script(file: str):
    if os.path.splitext(file)[1] == ".link":
        file = open(file, "r", encoding="utf-8").read().strip()

    if is_vscode_installed():
        workspace_file = create_myscript_workspace()
        open_in_vscode([workspace_file, file])
    else:
        open_code_editor([file])


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
    separated_path = script_path.split("/")
    if separated_path:
        matched_script_dir = next(
            filter(lambda x: x.name == separated_path[0], script_dirs), None
        )
        if matched_script_dir:
            separated_path[0] = matched_script_dir.path
    script_path = "/".join(separated_path)

    return script_path


def edit_script_config(script_path: str):
    default_config = get_default_script_config()

    script_config_file = get_script_config_file(script_path)
    if script_config_file is None:
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    script_config_file_path = get_script_config_file_path(script_path)

    def on_dict_update(dict):
        data = {k: v for k, v in dict.items() if default_config[k] != v}
        save_yaml(
            data,
            script_config_file_path,
        )

    config_edit_history_file = os.path.join(get_data_dir(), "config_edit_history.json")
    if os.path.exists(config_edit_history_file):
        with open(config_edit_history_file, "r") as f:
            config_edit_history = json.load(f)
    else:
        config_edit_history = {}

    def on_dict_history_update(config_edit_history: Dict[str, List[Any]]):
        with open(config_edit_history_file, "w", encoding="utf-8") as f:
            json.dump(config_edit_history, f, indent=2)

    script_config_file_rel_path = get_relative_script_path(script_config_file_path)
    w = DictEditMenu(
        data,
        default_dict=default_config,
        on_dict_update=on_dict_update,
        prompt=f"edit {script_config_file_rel_path}",
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

    if script_path.endswith(".user.js"):
        url = script.get_userscript_url()
        set_clip(url)
        logging.info("Copied url: %s" % url)

    elif ext == ".md" or ext == ".txt":
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
                variables = script.get_variables()
                if variables:
                    content = "{{ include('%s', %s) }}" % (
                        script_path,
                        variables,
                    )
                else:
                    content = "{{ include('%s') }}" % (script_path)
            else:
                content = "{{ include('%s') }}" % script_path
        else:
            raise Exception(f'Invalid format specified "{format}".')

        set_clip(content)
        return content


def create_new_script(ref_script_path=None, duplicate=False):
    label: str
    if duplicate:
        text = get_selected_script_path_rel(script_path=ref_script_path)
        label = "duplicate script"
    else:
        text = get_selected_script_dir_rel(script_path=ref_script_path)
        label = "new script:"
    w: Menu = Menu(prompt=label, text=text)
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
        if src_script_config_file is not None:
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
    replace_all_occurrence: bool = False,
):
    script_rel_path = get_relative_script_path(script_full_path)

    matched_files: List[str] = []
    if replace_all_occurrence:
        modified_lines = replace_script_str(
            script_rel_path,
            dry_run=True,
            matched_files=matched_files,
            on_progress=on_progress,
        )
        items = [f"{x[0]}:{x[1]}:\t{x[2]}" for x in modified_lines]
    else:
        items = []

    w = Menu(prompt="new name", text=script_rel_path, items=items)
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
    if replace_all_occurrence:
        replace_script_str(
            script_rel_path, new_script_rel_path, matched_files=matched_files
        )
    return True
