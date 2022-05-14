import os

from _android import setup_android_env, start_app
from _editor import open_in_vscode
from _git import git_clone
from _shutil import call_echo, cd, menu_item, menu_loop, setup_logger

setup_logger()
# run_elevated("choco install ninja -y")
# setup_cmake(cmake_version="3.10.2")
setup_android_env()

folder = git_clone("https://github.com/googlesamples/android-ndk")
print(folder)


@menu_item(key="g")
def build_gles3jni():
    cd(os.path.join(folder, "gles3jni"))
    call_echo("gradlew installDebug")
    start_app("com.android.gles3jni", use_monkey=True)


@menu_item(key="n")
def build_native_activity():
    cd(os.path.join(folder, "native-activity"))
    open_in_vscode(os.getcwd())
    call_echo("gradlew installDebug")
    start_app("com.example.native_activity", use_monkey=True)




if __name__ == "__main__":
    menu_loop()
