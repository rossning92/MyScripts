from _git import git_clone
from _shutil import shell_open

if __name__ == "__main__":
    # run_elevated('choco install ninja -y')
    # setup_cmake(cmake_version='3.10.2')
    # setup_android_env()

    git_clone("https://github.com/ARM-software/opengl-es-sdk-for-android")

    shell_open(".")

    # open_code_editor(os.getcwd())
