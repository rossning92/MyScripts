from subprocess import call
from _android import *
from _shutil import *

try:
    setup_android_env()
except:
    run_elevated('choco install android-sdk -y')
    setup_android_env()

packages = [
    'platforms;android-21',
    'platforms;android-24',
    'platforms;android-26',
    'build-tools;27.0.3',
    'lldb;3.1',
    'ndk-bundle'
]

for pkg in packages:
    call(['sdkmanager', pkg], shell=True)
