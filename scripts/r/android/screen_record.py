from _shutil import *
import signal

SCREEN_RECORD_MAX_SECS = '{{SCREEN_RECORD_MAX_SECS}}'
if SCREEN_RECORD_MAX_SECS == '':
    SCREEN_RECORD_MAX_SECS = 10
else:
    SCREEN_RECORD_MAX_SECS = int(SCREEN_RECORD_MAX_SECS)

signal.signal(signal.SIGINT, lambda a, b: None)

chdir('~/Desktop')

# call('adb shell "[ -e /sdcard/recording.mp4]; rm /sdcard/recording.mp4"')

print('Press Ctrl-C to stop recording...')

file = 'Recording_%s.mp4' % get_cur_time_str()
extra_args = f'--time-limit {SCREEN_RECORD_MAX_SECS} --bit-rate 8M'
call(f'adb shell screenrecord /sdcard/{file} {extra_args}', check_call=False)

call(f'adb pull /sdcard/{file}')
call(f'cmd /c start {file}')
