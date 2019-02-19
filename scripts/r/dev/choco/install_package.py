from _gui import search
import sys
import subprocess

pkg_list = [
    'miktex',
    'unity --version 2018.2.0',
    'sketchup',
    'blender',
    'graphviz',
    'inkscape',
]

dev = [
    'atom',
    'graphviz',
    'miniconda3',
    'pycharm-community',
    'cmake',
    'visualstudio2017community',
    'androidstudio',
    'android-sdk',
]

media = [
    'ffmpeg',
    'vlc',
    'imagemagick',
]

for_work = [
    'p4v',
    'selenium-chrome-driver',
]

pkg_list = sorted(['@for work'] + pkg_list + dev + media)

idx = search(pkg_list)
if idx < 0:
    sys.exit(1)

subprocess.call('choco source add --name=chocolatey --priority=-1 -s="https://chocolatey.org/api/v2/"')

if pkg_list[idx] == '@for work':
    for pkg in for_work + media + dev:
        subprocess.call('choco install %s -y' % pkg)
else:
    subprocess.call('choco install %s -y' % pkg_list[idx])
