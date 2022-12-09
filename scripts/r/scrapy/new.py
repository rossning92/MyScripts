from _conda import *
from _editor import *
from _shutil import *
import shutil
import webbrowser

PROJECT_NAME = "{{SCRAPY_PROJECT}}"


if not shutil.which("scrapy"):
    # https://docs.scrapy.org/en/latest/intro/install.html
    conda_shell_exec("conda install scrapy -y")
else:
    print("Scrapy installed already.")


cd("~/Projects/scrapy")

if not exists(PROJECT_NAME):
    conda_shell_exec("scrapy startproject %s" % PROJECT_NAME)
    cd(PROJECT_NAME)
    conda_shell_exec("scrapy genspider example example.com")
else:
    cd(PROJECT_NAME)

replace(
    f"{PROJECT_NAME}/settings.py", "ROBOTSTXT_OBEY = True", "ROBOTSTXT_OBEY = False"
)
append_line(f"{PROJECT_NAME}/settings.py", "FEED_EXPORT_ENCODING = 'utf-8'")


# open_in_editor(".")
# webbrowser.open("https://docs.scrapy.org/en/latest/")


while True:
    ch = getch()
    if ch == "c":
        conda_shell_exec("scrapy crawl example -o output.json")
