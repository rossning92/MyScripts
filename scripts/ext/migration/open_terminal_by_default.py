from _shutil import *
from _script import *

cd('../../')

for f in glob.glob('**/*.yaml', recursive=True):
    f = f.replace('\\', '/')

    if f.startswith('ext/'):
        continue

    data = load_meta_file(f)
    if 'newWindow' in data:
        print(f)

    data['newWindow'] = True

    save_meta_file(data, f)
