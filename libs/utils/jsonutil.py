import json
from typing import Any, Dict, List, Union


def load_json(
    file: str, default: Union[Dict[str, Any], List[Any], None] = None
) -> Union[Dict[str, Any], List[Any]]:
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
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
