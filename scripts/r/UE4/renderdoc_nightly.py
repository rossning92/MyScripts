import urllib.request
import os
import subprocess
from _shutil import *

INSTALL_DIR = r'C:\Tools\RenderDoc'

os.chdir(os.path.join(os.environ['USERPROFILE'], 'Downloads'))


def install_nightly():
    while True:
        try:
            from requests_html import HTMLSession

            break
        except:
            subprocess.call(
                ['python', '-m', 'pip', 'install', 'requests_html'])

    session = HTMLSession()

    r = session.get('https://renderdoc.org/builds')
    nodes = r.html.xpath(
        ".//a[contains(text(),'Nightly') and contains(text(),'ZIP')]")
    url = nodes[0].attrs['href']

    f = download(url)
    print(f)

    remove(INSTALL_DIR)
    unzip(f, INSTALL_DIR)


def install():
    download('https://renderdoc.org/stable/1.4/RenderDoc_1.4_64.msi',
             'RenderDoc_1.4_64.msi')
    call('msiexec /i RenderDoc_1.4_64.msi /quiet /qn /norestart')


def start_renderdoc():
    match = glob.glob(os.path.join(
        INSTALL_DIR, '**', 'qrenderdoc.exe'), recursive=True)
    if not match:
        return False

    start_process(match[0])

    return True


if not start_renderdoc():
    if '{{RENDERDOC_INSTALL_NIGHTLY}}':
        install_nightly()
    else:
        install()
