import os

from _android import setup_android_env
from _cmake import setup_cmake
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call_echo, cd, confirm, run_elevated

# Ninja is required
# run_elevated("choco install ninja -y")

setup_cmake(cmake_version="3.19.3")
setup_android_env(jdk_version="11.0")

# https://github.com/KhronosGroup/Vulkan-Samples#setup
git_clone("https://github.com/KhronosGroup/Vulkan-Samples")

call_echo("bldsys\\scripts\\generate_android_gradle.bat")

cd("build/android_gradle")

try:
    call_echo("gradle installDebug")
except Exception:
    if confirm("Re-run with more info?"):
        call_echo("gradle installDebug --info")

# open_in_vscode(os.getcwd())
