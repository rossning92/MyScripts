from _android import *

call2('adb wait-for-device')
# call2('adb root')
logcat(level='W|E|F')
