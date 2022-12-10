import logging
import os
import shutil

from _editor import open_in_editor
from _script import (
    get_absolute_script_path,
    get_all_scripts,
    get_my_script_root,
    get_relative_script_path,
    get_script_config_file,
    get_script_default_config,
    get_script_directories,
    get_script_root,
)
from _shutil import load_yaml, save_yaml, set_clip
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

    script_config_file = get_script_config_file(script_path)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    def on_dict_update(dict):
        data = {k: v for k, v in dict.items() if default_config[k] != v}
        save_yaml(data, script_config_file)

    w = DictEditWindow(
        data,
        default_dict=default_config,
        on_dict_update=on_dict_update,
        label="edit config",
    )
    ret = w.exec()
    if ret == -1:
        return False
    else:
        return True


def copy_script_path_to_clipboard(script_path):
    if script_path.endswith(".md"):
        with open(script_path, "r", encoding="utf-8") as f:
            set_clip(f.read())
        logging.info("Markdown content is copied to clipboard.")
    else:
        # Copy relative path
        script_path = get_relative_script_path(script_path)

        # Quote script path if it contains spaces
        if " " in script_path:
            script_path = '"' + script_path + '"'

        content = f"run_script {script_path}"
        set_clip(content)
        logging.info("Copied to clipboard: %s" % content)
        return content


def create_new_script(ref_script_path=None, duplicate=False):
    if duplicate:
        text = get_selected_script_path_rel(script_path=ref_script_path)
        label = "duplicate script"
    else:
        text = get_selected_script_dir_rel(script_path=ref_script_path)
        label = "new script"
    w = Menu(label=label, text=text)
    w.exec()
    dest_script = w.get_text()
    if not dest_script:
        return

    # Convert to abspath
    dest_script = get_absolute_script_path(dest_script)

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

    else:
        template_root = os.path.join(get_my_script_root(), "templates")
        if ext == ".py":
            shutil.copyfile(os.path.join(template_root, "python.py"), dest_script)
        elif ext == ".mmd":
            shutil.copyfile(os.path.join(template_root, "mermaid.mmd"), dest_script)
        else:
            # Create empty file
            with open(dest_script, "w") as _:
                pass

    edit_myscript_script(os.path.realpath(dest_script))
    return dest_script


def replace_script_str(old, new=None, dry_run=False):
    preview = []
    files = list(get_all_scripts())
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        dirty = False
        for i, line in enumerate(lines):
            if old in line:
                if dry_run:
                    preview.append([get_relative_script_path(file), i + 1, lines[i]])
                else:
                    lines[i] = line.replace(old, new)
                dirty = True

        if dirty and not dry_run:
            s = "\n".join(lines)
            with open(file, "w", encoding="utf-8") as f:
                f.write(s)

    return preview


def rename_script(script_full_path):
    script_rel_path = get_relative_script_path(script_full_path)
    preview = replace_script_str(script_rel_path, dry_run=True)
    preview = [str(x) for x in preview]

    w = Menu(label="new name", text=script_rel_path, items=preview)
    w.exec()
    new_script_rel_path = w.get_text()
    if not new_script_rel_path:
        return False

    # Rename script
    new_script_full_path = get_absolute_script_path(new_script_rel_path)
    os.makedirs(os.path.dirname(new_script_full_path), exist_ok=True)
    os.rename(script_full_path, new_script_full_path)

    # Rename config file if any
    config_file = os.path.splitext(script_full_path)[0] + ".config.yaml"
    new_config_file = os.path.splitext(new_script_full_path)[0] + ".config.yaml"
    if os.path.exists(config_file):
        os.rename(config_file, new_config_file)

    # Replace script string
    replace_script_str(script_rel_path, new_script_rel_path)
    return True
