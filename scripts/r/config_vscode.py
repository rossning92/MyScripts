from _shutil import *
import json

extensions = '''
donjayamanne.githistory
ms-python.python
ms-vscode.cpptools
stkb.rewrap
streetsidesoftware.code-spell-checker
shd101wyy.markdown-preview-enhanced
mdickin.markdown-shortcuts
'''

extensions = [x.strip() for x in extensions.splitlines()]
extensions = [x for x in extensions if x]

print2('Install extensions...')
for ext in extensions:
    call_echo('code --install-extension %s' % ext)

print2('Update key bindings...')
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

print2('Update user settings...')
setting_file = expandvars('%APPDATA%/Code/User/settings.json')
data = json.load(open(setting_file))
data['pasteImage.path'] = "${currentFileNameWithoutExt}"
data['workbench.editor.enablePreviewFromQuickOpen'] = False
json.dump(data, open(setting_file, 'w'), indent=4)
