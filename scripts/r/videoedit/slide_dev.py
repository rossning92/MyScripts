import os

from _script import run_script
from _shutil import get_files

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "slide"))

files = get_files()
if files:
    file = files[0]
else:
    file = "examples/%s.md" % os.environ["_TEMPLATE"]

run_script("r/web/open_in_browser_dev.py", ["http://localhost:1244/"])
run_script(
    "export.js",
    args=["-d", "-t", os.environ["_TEMPLATE"], "-i", file, "-p", "1244"],
)
