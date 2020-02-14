import urllib.request
import os
import subprocess
from _shutil import *

os.chdir(os.path.join(os.environ['USERPROFILE'], 'Downloads'))


def install_nightly():
    while True:
        try:
            from requests_html import HTMLSession

            break
        except:
            subprocess.call(['python', '-m', 'pip', 'install', 'requests_html'])

    session = HTMLSession()

    r = session.get('https://renderdoc.org/builds')
    nodes = r.html.xpath(".//a[contains(text(),'Nightly') and contains(text(),'ZIP')]")
    url = nodes[0].attrs['href']

    f = download(url)
    print(f)

    DEST = r'C:\Tools\RenderDoc'
    remove(DEST)
    unzip(f, DEST)


def install():
    download('https://renderdoc.org/stable/1.4/RenderDoc_1.4_64.msi', 'RenderDoc_1.4_64.msi')
    call('msiexec /i RenderDoc_1.4_64.msi /quiet /qn /norestart')


if '{{RENDERDOC_INSTALL_NIGHTLY}}':
    install_nightly()
else:
    install()
