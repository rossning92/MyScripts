from _shutil import *

files = os.environ['_FILES'].split('|')
print(files)

for f in files:
    args = ['adb', 'push', f, '/sdcard/']
    call(args)
