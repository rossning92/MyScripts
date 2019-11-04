from _shutil import *

INSTALL_FOLDER = r'C:\tools\scrcpy'
EXE_FILE = INSTALL_FOLDER + '\\scrcpy.exe'

if not exists(EXE_FILE) or r'{{_REINSTALL}}':
    chdir(gettempdir())
    download('https://github.com/Genymobile/scrcpy/releases/download/v1.10/scrcpy-win64-v1.10.zip', 'scrcpy.zip')
    mkdir(r'C:\tools\scrcpy')
    unzip('scrcpy.zip', r'C:\tools\scrcpy')

chdir(dirname(EXE_FILE))
call(EXE_FILE)
