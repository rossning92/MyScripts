import os
import threading

from _script import run_script
from _shutil import open_url

os.chdir("slide")


threading.Thread(target=lambda: open_url("http://localhost:1244")).start()

run_script(
    "export.js",
    args=["-d", "-t", "{{_TEMPLATE}}", "-i", "examples/{{_TEMPLATE}}.md", "-p", "1244"],
)

