import glob
import os

from _shutil import getch, print2

from cmake_build import cmake_build
from lint import lint

if __name__ == "__main__":
    project_dir = r"{{PROJECT_DIR}}"
    os.chdir(project_dir)

    lint(project_dir)

    if os.path.exists("CMakeLists.txt"):
        print2("Building using cmake...", color="green")
        cmake_build(project_dir)

    elif glob.glob("*.cpp") or glob.glob("*.c"):
        print2("Configure as a C++ project? (y/n)", color="green")
        if getch() == "y":
            cmake_build(project_dir)

