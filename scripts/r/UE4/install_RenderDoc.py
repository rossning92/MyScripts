import urllib.request
import os
import subprocess


def download(url):
    print('Downloading "%s" ...' % url)
    file_name = os.path.basename(url)
    urllib.request.urlretrieve(url, file_name)


os.chdir(os.path.join(os.environ['USERPROFILE'], 'Downloads'))

download('https://renderdoc.org/stable/1.1/RenderDoc_1.1_64.msi')

os.system('RenderDoc_1.1_64.msi')
