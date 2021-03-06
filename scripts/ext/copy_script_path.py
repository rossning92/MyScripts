from _shutil import *


script_path = os.environ["_SCRIPT"]

if script_path.endswith(".md"):
    with open(script_path, "r", encoding="utf-8") as f:
        set_clip(f.read())

    print("Content is copied to clipboard.")
else:
    # Copy relative path
    script_root = os.path.realpath(os.path.realpath(__file__) + "/../../")
    script_path = re.sub("^" + re.escape(script_root), "", script_path)
    script_path = script_path.replace("\\", "/")

    set_clip(script_path)
    print("Script path copied: %s" % script_path)
