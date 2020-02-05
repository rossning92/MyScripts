from _shutil import *
from _git import *
from _cmake import *

git_clone('https://github.com/android/ndk-samples')

run_elevated('choco install ninja -y')
setup_cmake(version='3.10.2')
