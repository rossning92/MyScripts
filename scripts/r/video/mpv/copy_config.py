from _shutil import *

if sys.platform == 'win32':
    if os.path.exists(expandvars('%APPDATA%\\mpv')):
        copy('mpv', expandvars('%APPDATA%/'))
