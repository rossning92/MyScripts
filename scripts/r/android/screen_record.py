from _shutil import *
import signal

signal.signal(signal.SIGINT, lambda a, b: None)

chdir('~/Desktop')

# call('adb shell "[ -e /sdcard/recording.mp4]; rm /sdcard/recording.mp4"')

print('Press Ctrl-C to stop recording...')

extra_args = '--time-limit 5 --bit-rate 8M'
call('adb shell screenrecord /sdcard/recording.mp4 ' + extra_args, check_call=False)

call('adb pull /sdcard/recording.mp4')
call('cmd /c start recording.mp4')
