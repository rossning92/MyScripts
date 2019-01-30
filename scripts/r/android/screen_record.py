from _shutil import *
import signal

signal.signal(signal.SIGINT, lambda a, b: None)

chdir('~/Desktop')

call('adb shell "[ -e /sdcard/recording.mp4]; rm /sdcard/recording.mp4"')

print('Press Ctrl-C to stop recording...')
call('adb shell screenrecord /sdcard/recording.mp4')

call('adb pull /sdcard/recording.mp4')
call('cmd /c start recording.mp4')

