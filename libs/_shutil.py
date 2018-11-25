from subprocess import call, check_output
import os
from os import chdir
from os.path import exists


def mkdir(path):
    os.makedirs(path, exist_ok=True)
