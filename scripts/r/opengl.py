from _shutil import *
import os
from _git import *

git_clone('https://github.com/JoeyDeVries/LearnOpenGL')

os.environ['PATH'] = r'C:\Program Files\CMake\bin' + os.pathsep + os.environ['PATH']
mkdir('build')
call(['cmake', '-G' 'Visual Studio 15 2017', '..'], cwd='build')
