from web.webscreenshot import webscreenshot
from md_to_html import convert_md_to_html
from _shutil import get_files, shell_open

f = get_files()[0]
f = convert_md_to_html(f)
f = webscreenshot(f)
shell_open(f)
