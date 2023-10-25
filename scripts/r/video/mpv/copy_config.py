import os
import sys

from _shutil import run_elevated

if sys.platform == "win32":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.expandvars("%APPDATA%\\mpv")):
        # copy('mpv', expandvars('%APPDATA%/'))
        mpv = os.path.join(script_dir, "_mpv")
        run_elevated(f'cmd /c MKLINK /D "%APPDATA%\\mpv" "{mpv}"')
