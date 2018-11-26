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
    'sketchup'
]

pkg_list = sorted(pkg_list)

idx = search(pkg_list)
if idx < 0:
    sys.exit(1)

subprocess.call('choco install %s -y' % pkg_list[idx])
