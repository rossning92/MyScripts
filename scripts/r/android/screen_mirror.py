from _shutil import *

bin_file = r'C:\tools\scrcpy-win64\scrcpy.exe'

if not exists(bin_file):
    chdir(gettempdir())
    download('https://github.com/Genymobile/scrcpy/releases/download/v1.8/scrcpy-win64-v1.8.zip', 'scrcpy.zip')
    unzip('scrcpy.zip', r'C:\tools')

chdir(dirname(bin_file))
Popen(bin_file)
