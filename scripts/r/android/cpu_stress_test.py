from _shutil import *

dd = ' | '.join(['dd if=/dev/zero of=/dev/null'] * 8)
args = 'adb shell "fulload() { %s & }; fulload; read; killall dd"' % dd
call2(args)
