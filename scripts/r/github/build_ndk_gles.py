from _shutil import *
from _git import *
from _android import *
from _editor import *
from _cmake import *

run_elevated('choco install ninja -y')
setup_cmake(version='3.10.2')
setup_android_env()

git_clone('https://github.com/googlesamples/android-ndk')

chdir('gles3jni')

call2('gradlew installDebug')

open_in_vscode(os.getcwd())
