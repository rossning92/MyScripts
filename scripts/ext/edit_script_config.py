import os
import sys

from _script import get_default_script_config_file, get_script_default_config
from _shutil import load_yaml, save_yaml
from _term import DictEditWindow

if __name__ == "__main__":
    default_config = get_script_default_config()

    script_path = os.environ["_SCRIPT"]
    script_config_file = get_default_script_config_file(script_path)
    if not os.path.exists(script_config_file):
        data = {}
    else:
        data = load_yaml(script_config_file)

    data = {**default_config, **data}

    def on_dict_update(dict):
        data = {k: v for k, v in dict.items() if default_config[k] != v}
        save_yaml(data, script_config_file)

    w = DictEditWindow(data, default_dict=default_config, on_dict_update=on_dict_update)
    ret = w.exec()

    if ret == -1:
        sys.exit(0)
