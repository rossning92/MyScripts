from _shutil import *

files = env['_FILES'].split('|')
assert len(files) == 2

vscode = r'C:\Program Files\Microsoft VS Code\Code.exe'
call([vscode, '--diff', files[0], files[1]])
