from _gui import search
import sys
import subprocess

pkg_list = [
    'androidstudio',
    'android-sdk',
    'p4v',
    'pycharm-community',
    'selenium-chrome-driver',
    'miktex',
    'unity --version 2018.2.0',
    'sketchup',
    'visualstudio2017community'
]

pkg_list = sorted(pkg_list)

idx = search(pkg_list)
if idx < 0:
    sys.exit(1)

subprocess.call('choco source add --name=chocolatey --priority=-1 -s="https://chocolatey.org/api/v2/"')
subprocess.call('choco install %s -y' % pkg_list[idx])
