from _shutil import *
from _git import *
from _android import *
from _editor import *

setup_android_env()

run_elevated('choco install ninja -y')

# Cmake
CMAKE_PATH = 'C:\\tools\\cmake-3.10.2-win64-x64'
if not exists(CMAKE_PATH):
    zip_file = expanduser('~/Downloads/cmake-3.10.2-win64-x64.zip')
    download('https://github.com/Kitware/CMake/releases/download/v3.10.2/cmake-3.10.2-win64-x64.zip',
             filename=zip_file)
    unzip(zip_file, 'C:\\tools')
prepend_to_path(CMAKE_PATH + os.path.sep + 'bin')

git_clone('https://github.com/googlesamples/android-ndk')

chdir('gles3jni')

call2('gradlew installDebug')

open_in_vscode(os.getcwd())
