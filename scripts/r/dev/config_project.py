import glob
import os

from _shutil import getch, print2, call_echo

from cmake_build import cmake_build
from lint import lint

if __name__ == "__main__":
    project_dir = r"{{PROJECT_DIR}}"
    os.chdir(project_dir)

    if "{{_LINT}}":
        lint(project_dir)

    if os.path.exists("CMakeLists.txt"):
        print2("Building using cmake...", color="green")
        cmake_build(project_dir)

    elif glob.glob("*.cpp") or glob.glob("*.c"):
        print2("Configure as a C++ project? (y/n)", color="green")
        if getch() == "y":
            cmake_build(project_dir)

    elif os.path.exists("gradlew") or os.path.exists("gradlew.bat"):
        print2("Building using gradle...", color="green")
        call_echo("gradlew assembleDebug")
        apk_files = glob.glob(os.path.join(".", "**", "*.apk"), recursive=True)
        for i, f in enumerate(apk_files):
            print("[%d] %s" % (i + 1, f))
