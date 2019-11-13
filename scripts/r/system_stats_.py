from _shutil import *

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
            out = [re.sub('\s+device', '', x) for x in out]
            devices = ' | '.join(out)
        except:
            pass

        sleep(5)


if __name__ == '__main__':
    threading.Thread(target=adb_device_stat).start()

    i = 0
    while True:
        print(psutil.cpu_percent(interval=1))
        print(devices)
        print(flush=True)
