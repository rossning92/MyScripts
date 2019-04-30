from _shutil import *

mkdir('~/Projects')
chdir('~/Projects')

if not exists('HotkeyR'):
    call('git clone https://github.com/rossning92/HotkeyR')
Popen(['AutoHotkeyU64.exe', expanduser('HotkeyR/HotkeyR.ahk')])
