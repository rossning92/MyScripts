from _shutil import *
from _android import *

try_import('psutil')
import psutil

devices = 'err'


def adb_device_stat():
    global devices

    while True:
        try:
            out = subprocess.check_output('adb devices', universal_newlines=True)
            out = out.splitlines()[1:]
            out = filter(lambda x: x, out)
            out = [x[:6] for x in out]
            devices = ' | '.join(out)
        except:
            devices = 'err'

        if not devices:
            devices = 'n/a'

        sleep(5)


if __name__ == '__main__':
    setup_android_env()

    threading.Thread(target=adb_device_stat).start()

    i = 0
    while True:
        print(psutil.cpu_percent(interval=1))
        print(devices)
        print(flush=True)
