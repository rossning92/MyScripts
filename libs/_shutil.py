from subprocess import call, check_output
import os
from os import chdir
from os.path import exists
import sys
import requests


def mkdir(path):
    os.makedirs(path, exist_ok=True)


def download(url, filename=None):

    if filename is None:
        filename = os.path.basename(url)

    if exists(filename):
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
