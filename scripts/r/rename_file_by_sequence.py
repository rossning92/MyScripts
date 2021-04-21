from _shutil import *
import datetime
from _term import *

wildcard = '{{_WILDCARD}}' if '{{_WILDCARD}}' else '*'
prefix = '{{_PREFIX}}'

os.chdir(os.environ['_CUR_DIR'])

new_file_names = {}
i = 1
for f in sorted(glob.glob(wildcard)):
    ext = os.path.splitext(f)[1]
    new_file_names[f] = '%s%03d%s' % (prefix, i, ext)
    i += 1

for k, v in new_file_names.items():
    print('%s => %s' % (k, v))

print2('Continue? (y/n)')
if getch() == 'y':
    for k, v in new_file_names.items():
        os.rename(k, v)
