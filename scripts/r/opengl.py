from _shutil import *
import os

chdir("{{PROJECT_DIR}}")
if not exists('LearnOpenGL'):
    call('git clone https://github.com/JoeyDeVries/LearnOpenGL.git')

chdir('LearnOpenGL')

os.environ['PATH'] = r'C:\Program Files\CMake\bin' + os.pathsep + os.environ['PATH']
mkdir('build')
call(['cmake', '-G' 'Visual Studio 15 2017', '..'], cwd='build')
