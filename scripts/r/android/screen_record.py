from _shutil import *
import signal

signal.signal(signal.SIGINT, lambda a, b: None)

chdir('~/Desktop')

# call('adb shell "[ -e /sdcard/recording.mp4]; rm /sdcard/recording.mp4"')

print('Press Ctrl-C to stop recording...')

file = 'Recording_%s.mp4' % get_cur_time_str()
extra_args = '--time-limit 5 --bit-rate 8M'
call(f'adb shell screenrecord /sdcard/{file} {extra_args}', check_call=False)

call(f'adb pull /sdcard/{file}')
call(f'cmd /c start {file}')
