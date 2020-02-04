from _shutil import *
import json


print2('Update key bindings...')
with open(expandvars('%APPDATA%/Code/User/keybindings.json'), 'w') as f:
    f.write('''
[
    {
        "key": "ctrl+shift+v",
        "command": "markdown-preview-enhanced.openPreviewToTheSide",
        "when": "editorLangId == 'markdown'"
    },
    {
        "key": "shift+alt+r",
        "command": "revealFileInOS",
    }
]
    '''.strip())


print2('Update settings...')
f = expandvars('%APPDATA%/Code/User/settings.json')
data = json.load(open(f))
data['python.pythonPath'] = sys.executable.replace('\\', '/')
data['cSpell.enabledLanguageIds'] = ['markdown', 'text']
json.dump(data, open(f, 'w'), indent=4)


print2('Install extensions...')
extensions = [
    'donjayamanne.githistory',
    'ms-python.python',
    'ms-vscode.cpptools',
    'stkb.rewrap',
    'streetsidesoftware.code-spell-checker',

    # Markdown
    'shd101wyy.markdown-preview-enhanced',
    'mdickin.markdown-shortcuts',
]

for ext in extensions:
    call_echo('code --install-extension %s' % ext)


print2('Update user settings...')
setting_file = expandvars('%APPDATA%/Code/User/settings.json')
data = json.load(open(setting_file))
data['pasteImage.path'] = "${currentFileNameWithoutExt}"
data['workbench.editor.enablePreviewFromQuickOpen'] = False
json.dump(data, open(setting_file, 'w'), indent=4)
