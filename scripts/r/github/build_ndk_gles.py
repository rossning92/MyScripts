from _shutil import *
from _git import *
from _android import *
from _cmake import *

setup_android_env()
setup_cmake()
run_elevated('choco install ninja -y')

git_clone('https://github.com/googlesamples/android-ndk')

chdir('gles3jni')

call2('gradlew installDebug')

# NDK
# Cmake https://github.com/Kitware/CMake/releases/tag/v3.10.2
# Ninja
