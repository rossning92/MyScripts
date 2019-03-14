from subprocess import check_call
import datetime
import os

os.chdir(os.path.expanduser('~/Desktop'))

file_name = datetime.datetime.now().strftime('Screenshot_%y%m%d%H%M%S.png')

print('Taking screenshot ...')
check_call(['adb', 'shell', 'screencap -p /sdcard/%s' % file_name])
check_call(['adb', 'pull', '-a', '/sdcard/%s' % file_name])
check_call(['adb', 'shell', 'rm /sdcard/%s' % file_name])

os.system(file_name)