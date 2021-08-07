import os

from _android import setup_android_env
from _cmake import setup_cmake
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call2, cd, run_elevated

# run_elevated("choco install ninja -y")
setup_cmake()
setup_android_env()

git_clone("https://github.com/KhronosGroup/Vulkan-Samples")

call2("bldsys\\scripts\\generate_android_gradle.bat")

cd("build/android_gradle")

call2("gradle installDebug")

# open_in_vscode(os.getcwd())
