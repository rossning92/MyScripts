from os import environ, pathsep
from os.path import expanduser, exists
import subprocess

conda_path = []

if exists(expanduser(r'~/Anaconda3')):
    conda_path += [
        expanduser(r'~/Anaconda3'),
        expanduser(r'~/Anaconda3/Scripts')
    ]

elif exists(r'C:\tools\miniconda3'):
    conda_path += [
        r'C:\tools\miniconda3',
        r'C:\tools\miniconda3\Scripts'
    ]

# Prepend anaconda to PATH
environ["PATH"] = pathsep.join(conda_path) + pathsep + environ["PATH"]
subprocess.call('cmd /c start')
