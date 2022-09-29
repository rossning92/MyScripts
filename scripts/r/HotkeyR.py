from _shutil import *

mkdir('~/Projects')
chdir('~/Projects')

if not exists('HotkeyR'):
    print('Cloning HotkeyR...')
    call('git clone https://github.com/rossning92/HotkeyR')

print('Starting HotkeyR...')
Popen(['AutoHotkeyU64.exe', expanduser('HotkeyR/HotkeyR.ahk')])
