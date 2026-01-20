import os

from _code import replace
from _pyenv import setup_py27
from _shutil import call_echo, cd, download, mkdir
from utils.android import setup_android_env

setup_android_env()

mk = """
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE     := getevent
LOCAL_SRC_FILES  := getevent.c

include $(BUILD_EXECUTABLE)
"""

project_dir = "~/Desktop/getevent"
mkdir(project_dir)
cd(project_dir)

# Download files
if not os.path.exists("jni"):
    mkdir("jni")
    cd("jni")

    with open("Android.mk", "w") as f:
        f.write(mk)

    download(
        "https://raw.githubusercontent.com/aosp-mirror/platform_system_core/master/toolbox/getevent.c"
    )
    replace("getevent.c", "getevent_main", "main")

    download(
        "https://raw.githubusercontent.com/aosp-mirror/platform_system_core/master/toolbox/generate-input.h-labels.py"
    )
    call_echo("python generate-input.h-labels.py > input.h-labels.h")

# Build
setup_py27()
cd(project_dir)
call_echo("ndk-build")

# Run
cd(project_dir + "/obj/local/armeabi-v7a")
call_echo("adb push getevent /data/local/tmp")
call_echo("adb shell chmod 777 /data/local/tmp/getevent")
call_echo("adb shell /data/local/tmp/getevent")
