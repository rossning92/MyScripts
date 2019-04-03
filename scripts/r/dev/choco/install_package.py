from _gui import search
import sys
import subprocess

other = [
    'miktex',
    'unity --version 2018.2.0',
    'unity --version 2018.2.14',
    'sketchup',
    'blender',
    'graphviz',
    'inkscape',
]

dev = [
    'atom',
    'graphviz',
    'anaconda3',
    'miniconda3',
    'pycharm-community',
    'cmake',
    'visualstudio2017community',
    'androidstudio',
    'android-sdk',
    'llvm',
    'ripgrep',
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

other_options = [
    '@for work',
]

redist = [
    'dotnet4.5',
]

pkg_list = sorted(other_options + other + dev + media + redist)
idx = search(pkg_list)
if idx < 0:
    sys.exit(1)

subprocess.call('choco source add --name=chocolatey --priority=-1 -s="https://chocolatey.org/api/v2/"')

if pkg_list[idx] == '@for work':
    for pkg in for_work + media + dev:
        subprocess.call('choco install %s -y' % pkg)
else:
    subprocess.call('choco install %s -y' % pkg_list[idx])
