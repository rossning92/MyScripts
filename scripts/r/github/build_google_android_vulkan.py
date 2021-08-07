import os

from _android import setup_android_env
from _cmake import setup_cmake
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call2, cd, run_elevated, call_echo

# run_elevated("choco install ninja -y")
setup_cmake()
setup_android_env()

git_clone("https://github.com/googlesamples/android-vulkan-tutorials")

cd("tutorial05_triangle")

call_echo("gradlew installDebug")

call_echo("adb shell am start -n com.google.vulkan.tutorials.five/android.app.NativeActivity")

open_in_vscode(os.getcwd())
