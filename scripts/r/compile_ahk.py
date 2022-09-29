from _shutil import *

script_file = get_files(cd=True)[0]

call2(f'"C:\Program Files\AutoHotkey\Compiler\Ahk2Exe.exe" /in "{script_file}" /icon "Icon.ico"')
call2('ie4uinit.exe -ClearIconCache')
call2('ie4uinit.exe -Show')