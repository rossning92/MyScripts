from _shutil import *
import re
import time


def wait_for_disconnect():
    print('Please disconnect the device via USB...')
    while True:
        try:
            subprocess.check_output('adb wait-for-device', stderr=subprocess.STDOUT)
            break
        except subprocess.CalledProcessError as e:
            err_str = e.output.decode()
            if 'more than one' in err_str:
                time.sleep(1)
            else:
                raise e


def connect_device_over_wifi():
    call2('adb disconnect')

    print('Please connect the device via USB...')
    call2('adb wait-for-device')

    print('Get IP address of wlan0...')
    s = check_output('adb -d shell "ifconfig wlan0"').decode()
    match = re.search(r'inet addr:([^ ]+)', s)
    if match is None:
        raise Exception('Cannot find wlan IP address.')
    ip = match.group(1)

    print('Start adb server in tcp mode...')
    call2('adb -d tcpip 5555')
    call2('adb wait-for-device')

    print('Connect to device over wifi...')
    out = check_output(f'adb connect %s:5555' % ip, shell=True).decode().strip()
    print(out)
    if 'failed' in out:
        raise Exception(out)

    wait_for_disconnect()


connect_device_over_wifi()
