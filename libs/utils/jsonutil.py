import json
import os
import shutil
from typing import Optional, Tuple, TypeVar

T = TypeVar("T")


def load_json(
    file: str,
    default: Optional[T] = None,
) -> T:
    try:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if default is not None and isinstance(default, dict):
                data = {**default, **data}
            return data
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        if default is not None:
            return default
        else:
            raise Exception("Default value is not specified.")


def save_json(file: str, data):
    file = os.path.abspath(file)
    dir_path = os.path.dirname(file)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def try_load_json(
    file: str,
    last_mtime: float,
    default: Optional[T] = None,
) -> Optional[Tuple[T, float]]:
    # Check if the file has been modified since last time
    mtime = os.path.getmtime(file)
    if mtime <= last_mtime:
        return None

    return load_json(file=file, default=default), mtime


def try_save_json(file: str, data, last_mtime: float, backup=False):
    # Check if the file has been externally modified
    if os.path.exists(file):
        mtime = os.path.getmtime(file)
        if mtime < last_mtime:
            raise RuntimeError("JSON file has been modified externally")

    # Backup JSON file
    if backup and os.path.exists(file):
        shutil.copy(file, file + ".bak")

    # Save JSON file
    save_json(file=file, data=data)

    # Return modified time
    return os.path.getmtime(file)
