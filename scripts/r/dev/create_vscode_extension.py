from _shutil import *

setup_nodejs()


cd('~/.vscode/extensions')

call2('yarn add global yo generator-code')
call2('yo code')
