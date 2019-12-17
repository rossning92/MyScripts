from _shutil import *
import datetime
from _term import *

os.chdir(os.environ['CURRENT_FOLDER'])

new_file_names = {}
for f in glob.glob('*'):
    time_str = time.strftime('%y%m%d%H%M%S', time.gmtime(os.path.getmtime(f)))
    assert time_str not in new_file_names

    ext = os.path.splitext(f)[1]

    new_file_names[f] = time_str + ext

for k, v in new_file_names.items():
    print('%s => %s' % (k, v))

print('Press Y to continue')
if getch() == 'y':
    for k, v in new_file_names.items():
        os.rename(k, v)
