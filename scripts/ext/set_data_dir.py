import os
from pathlib import Path

from utils.menu.filemgr import FileManager

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_dir = (Path(script_dir) / ".." / ".." / "config").resolve()
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    config_file = os.path.join(config_dir, "data_dir.txt")

    cur_path = None
    if os.path.exists(config_file):
        with open(config_file) as f:
            cur_path = f.read()

    path = FileManager(goto=cur_path, prompt="Set data dir to:").select_directory()
    if path is not None:
        with open(config_file, "w") as f:
            f.write(path)
