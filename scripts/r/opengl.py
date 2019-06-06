from _shutil import *
import os

proj_dir = r"{{PROJECT_DIR}}"
if not proj_dir:
    proj_dir = "C:\\Projects"

chdir(proj_dir)
if not exists('LearnOpenGL'):
    call('git clone https://github.com/JoeyDeVries/LearnOpenGL.git')

chdir('LearnOpenGL')

os.environ['PATH'] = r'C:\Program Files\CMake\bin' + os.pathsep + os.environ['PATH']
mkdir('build')
call(['cmake', '-G' 'Visual Studio 15 2017', '..'], cwd='build')
