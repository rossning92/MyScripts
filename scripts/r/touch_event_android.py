from _shutil import *
from _setup_android_env import setup_android_env

prj_folder = r'C:\Projects'
mkdir(prj_folder)
chdir(prj_folder)

if not exists('minitouch'):
    call('git clone https://github.com/openstf/minitouch')

chdir('minitouch')
call('git submodule init')
call('git submodule update')

if False:
    setup_android_env()
    call('ndk-build')

exec_bash(r'''
adb shell getprop ro.product.cpu.abi | tr -d '\r'
ABI=$(adb shell getprop ro.product.cpu.abi | tr -d '\r')
adb push libs/$ABI/minitouch /data/local/tmp/
adb shell chmod +x /data/local/tmp/minitouch
adb shell /data/local/tmp/minitouch -h
''')
