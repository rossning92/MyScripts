from _shutil import *

mkdir('~/Projects')
chdir('~/Projects')

call('git clone %s --depth=1' % '{{GIT_URL}}')
call('start .')
