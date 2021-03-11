from _shutil import *

files = get_files()
assert len(files) == 2

vscode = r"C:\Program Files\Microsoft VS Code\Code.exe"
call([vscode, "--diff", files[0], files[1]])
