from _shutil import *
from _git import *
from _android import *
from _editor import *
from _cmake import *

# run_elevated('choco install ninja -y')
# setup_cmake(version='3.10.2')
# setup_android_env()

git_clone('https://github.com/ARM-software/opengl-es-sdk-for-android')

shell_open('.')

# open_in_vscode(os.getcwd())
