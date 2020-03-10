from _shutil import *
from _term import *

new_file = wait_for_new_file(os.path.expandvars(
    r'%USERPROFILE%\Videos\Desktop\*.mp4'))

file_name = input('input file name (no ext): ')
if not file_name:
    print2('Discard %s.' % new_file, color='red')
    os.remove(new_file)

file_name = slugify(file_name)
os.makedirs('screencap', exist_ok=True)
file_name = 'screencap/' + file_name + '.mp4'
os.rename(new_file, file_name)
print2('file saved: %s' % file_name, color='green')

clip = '<!-- video: %s -->' % file_name
set_clip(clip)
