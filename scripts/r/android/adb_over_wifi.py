from _shutil import *
import re

s = check_output('adb -d shell ifconfig wlan0').decode()
match = re.findall(r'inet addr:([^ ]+)', s)
ip = match[0]

call('adb -d tcpip 5555')
call(f'adb connect {ip}:5555')
