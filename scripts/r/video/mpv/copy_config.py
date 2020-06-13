from _shutil import *

if sys.platform == 'win32':
    if not os.path.exists(expandvars('%APPDATA%\\mpv')):
        # copy('mpv', expandvars('%APPDATA%/'))
        mpv = os.path.abspath('./_mpv')
        run_elevated(f'cmd /c MKLINK /D "%APPDATA%\\mpv" "{mpv}"')
