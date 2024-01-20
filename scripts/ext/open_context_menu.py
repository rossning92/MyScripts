import argparse
import re
from typing import List

from _script import Script, get_all_scripts, load_script_config
from utils.menu import Menu

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=str)
    args = parser.parse_args()

    matched_script: List[str] = []
    for script_path in get_all_scripts():
        config = load_script_config(script_path)
        patt = config["matchClipboard"]
        if patt and re.search(patt, args.text):
            print(script_path)
            matched_script.append(script_path)

    menu = Menu(prompt=f"script for: {args.text}", items=matched_script)
    menu.exec()
    script_path = menu.get_selected_item()
    if script_path is not None:
        script = Script(script_path)
        script.execute(args=[args.text])
