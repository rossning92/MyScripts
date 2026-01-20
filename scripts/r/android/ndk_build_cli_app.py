from _shutil import *
from utils.android import *

src_file = None
TARGET = "{{_TARGET}}" if "{{_TARGET}}" else "testapp"
f = get_files()[0]
if f.endswith(".c"):
    TARGET = os.path.splitext(os.path.basename(f))[0]
    src_file = f


def run(target):
    call2(f"adb push obj/local/armeabi-v7a/{target} /data/local/tmp")
    call2(f"adb shell chmod 777 /data/local/tmp/{target}")
    print2("Start %s" % target)
    call2(f"adb shell /data/local/tmp/{target}")


setup_android_env()

make_and_change_dir(expanduser("~/Projects/{{_TARGET}}"))

mkdir("jni")

write_text_file(
    f"""
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE     := {TARGET}
LOCAL_SRC_FILES  := {TARGET}.c

include $(BUILD_EXECUTABLE)
""",
    "jni/Android.mk",
)

if src_file:
    copy(src_file, f"jni/{TARGET}.c")
else:
    write_text_file(
        """
#include <stdio.h>
int main()
{
	printf( "Hello World" );
    return 0;
}
""",
        f"jni/{TARGET}.c",
        overwrite=False,
    )

write_text_file(
    """
APP_ABI := armeabi-v7a arm64-v8a
""",
    "jni/Application.mk",
)

call2("ndk-build")


run(TARGET)
