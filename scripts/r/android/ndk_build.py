from _shutil import *
from _android import *

android_mk = '''
LOCAL_PATH := $(call my-dir)
 
include $(CLEAR_VARS)
 
LOCAL_MODULE     := getevent
LOCAL_SRC_FILES  := getevent.c
 
include $(BUILD_EXECUTABLE)
'''.strip()

setup_android_env()

make_and_change_dir(expanduser('~/Projects/test_ndk_project'))

mkdir('jni')
with open('jni/Android.mk', 'w') as f:
    f.write(android_mk)

call2('ndk-build')

subprocess.call('explorer .')
