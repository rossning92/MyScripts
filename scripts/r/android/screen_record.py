from _shutil import *
import signal

max_secs = '{{_MAX_SECS}}'
if not max_secs:
    max_secs = 10
else:
    max_secs = int(max_secs)

signal.signal(signal.SIGINT, lambda a, b: None)

chdir('~/Desktop')

# call('adb shell "[ -e /sdcard/recording.mp4]; rm /sdcard/recording.mp4"')

print('Press Ctrl-C to stop recording...')

file = 'Recording_%s.mp4' % get_cur_time_str()
extra_args = f'--time-limit {max_secs} --bit-rate 8M'

if '{{_SIZE}}':
    extra_args += ' --size {{_SIZE}}' 

call(f'adb shell screenrecord /sdcard/{file} {extra_args}', check_call=False)

call(f'adb pull /sdcard/{file}')
call(f'cmd /c start {file}')
