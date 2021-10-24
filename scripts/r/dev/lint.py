import os

from _shutil import call_echo


def lint(project_dir):
    cmakelist = os.path.join(project_dir, "CMakeLists.txt")
    if os.path.exists(cmakelist):
        call_echo(["cmake-format", cmakelist, "-i"])


if __name__ == "__main__":
    project_dir = r"{{_PROJECT_DIR}}"
    lint(project_dir)
