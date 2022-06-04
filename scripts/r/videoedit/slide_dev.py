import os
import threading

from _script import run_script
from _shutil import open_url

os.chdir("slide")


run_script("r/web/open_in_browser_dev.py", ["http://localhost:1244/"])
run_script(
    "export.js",
    args=["-d", "-t", "{{_TEMPLATE}}", "-i", "examples/{{_TEMPLATE}}.md", "-p", "1244"],
)

