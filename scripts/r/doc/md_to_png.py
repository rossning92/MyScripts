from _shutil import get_files
from md_to_html import convert_md_to_html
from utils.shutil import shell_open
from web.webscreenshot2 import webscreenshot

if __name__ == "__main__":
    f = get_files()[0]
    f = convert_md_to_html(f)
    f = webscreenshot(f)
    shell_open(f)
