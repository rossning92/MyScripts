from _shutil import *

mkdir('~/Projects')
chdir('~/Projects')

folder = os.path.basename('{{GIT_URL}}')
if not exists(folder):
    call('git clone %s --depth=1' % '{{GIT_URL}}')

open_directory(folder)
