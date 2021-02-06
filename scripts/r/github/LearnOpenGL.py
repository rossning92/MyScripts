from _shutil import *
import os
from _git import *
from _cmake import *

git_clone('https://github.com/JoeyDeVries/LearnOpenGL')

setup_cmake()

mkdir('build')
subprocess.check_call(
    ['cmake', '-G' 'Visual Studio 15 2017', '..'], cwd='build', shell=True)
call2('build\\LearnOpenGL.sln', check=False)
