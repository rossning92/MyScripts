from utils.jsonutil import load_json
from utils.script.path import get_script_dirs_config_file


def main():
    config_path = get_script_dirs_config_file()
    data = load_json(config_path, default=[])
    for entry in data:
        print(entry["directory"])


if __name__ == "__main__":
    main()
