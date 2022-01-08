import os

from _android import setup_android_env
from _cmake import setup_cmake
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call2, cd, run_elevated

# run_elevated("choco install ninja -y")
# setup_cmake(cmake_version="3.10.2")
setup_android_env()

git_clone("https://github.com/googlesamples/android-ndk")

cd("gles3jni")

call2("gradlew installDebug")

open_in_vscode(os.getcwd())
