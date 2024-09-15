import subprocess
import sys

try:
    import yaml
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "pyyaml"])

import yaml


def load_yaml(file: str):
    with open(file, "r", encoding="utf-8") as f:
        return yaml.load(f.read(), Loader=yaml.FullLoader)


def save_yaml(data, file: str):
    with open(file, "w", encoding="utf-8", newline="\n") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def update_yaml(file, dict_):
    data = load_yaml(file)
    data.update(dict_)
    save_yaml(data, file)
