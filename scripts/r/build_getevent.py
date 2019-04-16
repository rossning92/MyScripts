from _shutil import *
from _pyenv import *
import _setup_android_env; _setup_android_env.setup_android_env()

mk = '''
LOCAL_PATH := $(call my-dir)
 
include $(CLEAR_VARS)
 
LOCAL_MODULE     := getevent
LOCAL_SRC_FILES  := getevent.c
 
include $(BUILD_EXECUTABLE)
'''

project_dir = '~/Desktop/getevent'
mkdir(project_dir)
chdir(project_dir)

# Download files
if not exists('jni'):
    mkdir('jni')
    chdir('jni')

    with open('Android.mk', 'w') as f:
        f.write(mk)

    download('https://raw.githubusercontent.com/aosp-mirror/platform_system_core/master/toolbox/getevent.c')
    replace('getevent.c', 'getevent_main', 'main')

    download(
        'https://raw.githubusercontent.com/aosp-mirror/platform_system_core/master/toolbox/generate-input.h-labels.py')
    call('python generate-input.h-labels.py > input.h-labels.h')

# Build
setup_py27()
chdir(project_dir)
call('ndk-build')

# Run
chdir(project_dir + '/obj/local/armeabi-v7a')
call('adb push getevent /data/local/tmp')
call('adb shell chmod 777 /data/local/tmp/getevent')
call('adb shell /data/local/tmp/getevent')
