from _shutil import *

files = os.environ['FILES_'].split('|')
print(files)

for f in files:
    args = ['adb', 'push', f, '/sdcard/']
    call(args)
