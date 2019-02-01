from subprocess import call
import datetime
import os

os.chdir(os.path.expanduser('~'))

file_name = datetime.datetime.now().strftime('Screenshot_%y%m%d%H%M%S.png')

print('Taking screenshot ...')
call(['adb', 'shell', 'screencap -p /sdcard/%s' % file_name])
call(['adb', 'pull', '-a', '/sdcard/%s' % file_name])
call(['adb', 'shell', 'rm /sdcard/%s' % file_name])

os.system(file_name)