from _shutil import run_elevated
import sys
import os

if sys.platform == "win32":
    if not os.path.exists(os.path.expandvars("%APPDATA%\\mpv")):
        # copy('mpv', expandvars('%APPDATA%/'))
        mpv = os.path.abspath("./_mpv")
        run_elevated(f'cmd /c MKLINK /D "%APPDATA%\\mpv" "{mpv}"')
