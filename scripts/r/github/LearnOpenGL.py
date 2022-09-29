import os

from _cpp import *
from _git import *
from _shutil import *

git_clone("https://github.com/JoeyDeVries/LearnOpenGL")

setup_cmake()

mkdir("build")
subprocess.check_call(
    ["cmake", "-G" "Visual Studio 16 2019", ".."], cwd="build", shell=True
)
call2("build\\LearnOpenGL.sln", check=False)
