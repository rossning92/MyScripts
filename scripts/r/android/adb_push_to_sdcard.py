from _shutil import *

files = os.environ['SELECTED_FILES'].split('|')
print(files)

for f in files:
    args = ['adb', 'push', f, '/sdcard/']
    call(args)