from _shutil import *


extensions = '''
donjayamanne.githistory
ms-python.python
ms-vscode.cpptools
stkb.rewrap
'''

extensions = [x for x in extensions.splitlines()]
extensions = [x.strip() for x in extensions]
extensions = [x for x in extensions if x]

for ext in extensions:
    call2('code --install-extension %s' % ext)