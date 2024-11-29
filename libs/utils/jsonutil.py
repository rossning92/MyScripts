import json


def load_json(file: str, default=None):
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        if default is not None:
            return default
        else:
            raise Exception("Default value is not specified.")


def save_json(file: str, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
