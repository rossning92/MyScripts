from subprocess import call, check_output
import os
from os import chdir
from os.path import exists, expanduser, expandvars
import sys
from shutil import copytree, rmtree
import shutil

try:
    import requests
except:
    call('pip install requests')
    import requests


def mkdir(path):
    os.makedirs(path, exist_ok=True)


def download(url, filename=None):
    if filename is None:
        filename = os.path.basename(url)

    if exists(filename):
        print('File already exists: %s' % filename)
        return

    print('Download: %s' % url)
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total / 1000), 1024 * 1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total)
                sys.stdout.write('\r[{}{}]'.format('█' * done, '.' * (50 - done)))
                sys.stdout.flush()
    sys.stdout.write('\n')


def copy(src, dst):
    if dst.endswith('/') or dst.endswith('\\'):
        mkdir(dst)
        shutil.copy(src, dst)
