from _shutil import *
from _android import *


def run(target):
    call2(f'adb push obj/local/armeabi-v7a/{target} /data/local/tmp')
    call2(f'adb shell chmod 777 /data/local/tmp/{target}')
    call2(f'adb shell /data/local/tmp/{target}')


setup_android_env()

make_and_change_dir(expanduser('~/Projects/test_ndk_project'))

mkdir('jni')

write_text_file('''
LOCAL_PATH := $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE     := testapp
LOCAL_SRC_FILES  := testapp.c

include $(BUILD_EXECUTABLE)
''', 'jni/Android.mk')

write_text_file('''
#include <stdio.h>
int main()
{
	printf( "Hello World" );
    return 0;
}
''', 'jni/testapp.c')

write_text_file('''
APP_ABI := armeabi-v7a arm64-v8a
''', 'jni/Application.mk')

call2('ndk-build')


run('testapp')
