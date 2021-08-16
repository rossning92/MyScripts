import os
from _script import run_script
from _browser import open_page
import threading

os.chdir("slide")


threading.Thread(target=lambda: open_page("http://localhost:1244")).start()

run_script(
    "export.js",
    args=["-d", "-t", "{{_TEMPLATE}}", "-i", "examples/{{_TEMPLATE}}.md", "-p", "1244"],
)

