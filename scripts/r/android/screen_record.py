from _shutil import *
import signal


def screen_cap(max_secs=10, bit_rate='20M'):
    signal.signal(signal.SIGINT, lambda a, b: None)

    print('Press Ctrl-C to stop recording...')

    file = 'Recording_%s.mp4' % get_cur_time_str()
    extra_args = f'--time-limit {max_secs} --bit-rate {bit_rate}'

    if '{{_SIZE}}':
        extra_args += ' --size {{_SIZE}}'

    call(
        f'adb shell screenrecord /sdcard/{file} {extra_args}', check_call=False)

    call(f'adb pull /sdcard/{file}')
    call(f'cmd /c start {file}')


if __name__ == '__main__':
    chdir('~/Desktop')

    screen_cap(
        max_secs=int('{{_MAX_SECS}}') if '{{_MAX_SECS}}' else 10,
        bit_rate='{{_BIT_RATE}}' if '{{_BIT_RATE}}' else '20M'
    )
