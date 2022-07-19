import os
import re

from _shutil import set_clip

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]

    if script_path.endswith(".md"):
        with open(script_path, "r", encoding="utf-8") as f:
            set_clip(f.read())

        print("Content is copied to clipboard.")
    else:
        # Copy relative path
        script_root = os.path.realpath(os.path.realpath(__file__) + "/../../")
        script_path = re.sub("^" + re.escape(script_root), "", script_path)
        script_path = script_path.replace("\\", "/").lstrip("/")

        set_clip(f"run_script {script_path}")
        print("Copied to clipboard: %s" % script_path)
