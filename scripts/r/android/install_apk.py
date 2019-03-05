from _shutil import *

apk = os.environ['SELECTED_FILE']
assert os.path.splitext(apk)[1].lower() == '.apk'

print('Installing apk...')
call(['adb', 'install', '-r', apk])
