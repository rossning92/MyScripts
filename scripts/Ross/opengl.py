from subprocess import call
import os

os.chdir("{{PROJECT_DIR}}")
if not os.path.exists('LearnOpenGL'):
    call('git clone https://github.com/JoeyDeVries/LearnOpenGL.git')

os.chdir('LearnOpenGL')

os.environ['PATH'] = r'C:\Program Files\CMake\bin' + os.pathsep + os.environ['PATH']
os.makedirs('build', exist_ok=True)
call(['cmake', '-G' 'Visual Studio 15 2017', '..'], cwd='build')
