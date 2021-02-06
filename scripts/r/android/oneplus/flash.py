from _shutil import *
from _android import *

# https://forum.xda-developers.com/oneplus-5t/how-to/official-oxygenos-4-7-2-7-1-1-ota-t3709265
# https://www.thecustomdroid.com/install-twrp-root-oneplus-5-5t-android-pie-oxygenos/


setup_android_env()

call2('adb shell twrp decrypt 123475')
