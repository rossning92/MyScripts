from _shutil import *

extensions = '''
donjayamanne.githistory
ms-python.python
ms-vscode.cpptools
stkb.rewrap
shd101wyy.markdown-preview-enhanced
'''

extensions = [x for x in extensions.splitlines()]
extensions = [x.strip() for x in extensions]
extensions = [x for x in extensions if x]

for ext in extensions:
    call2('code --install-extension %s' % ext)

with open(expandvars('%APPDATA%/Code/User/keybindings.json'), 'w') as f:
    f.write('''
[
    {
        "key": "ctrl+shift+v",
        "command": "markdown-preview-enhanced.openPreviewToTheSide",
        "when": "editorLangId == 'markdown'"
    }
]
    '''.strip())
