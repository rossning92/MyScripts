import os
from typing import Dict, Literal

from _filelock import FileLock

from utils.jsonutil import load_json, save_json
from utils.script.path import get_data_dir


def _get_status_file():
    return os.path.join(get_data_dir(), "script_status.json")


ScriptStatus = Literal["done", "error", "running"]


def set_script_status(name: str, status: ScriptStatus):
    status_file = _get_status_file()
    with FileLock("script_status"):
        data = load_json(status_file, default={})
        data[name] = status
        save_json(status_file, data)


def get_script_status() -> Dict[str, ScriptStatus]:
    status_file = _get_status_file()
    with FileLock("script_status"):
        return load_json(status_file, default={})
