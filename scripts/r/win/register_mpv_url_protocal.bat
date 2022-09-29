@echo off

:: Setup URL protocol for vlc://
reg add HKEY_CLASSES_ROOT\vlc /v "URL Protocol" /t REG_SZ /d "" /f
reg add HKEY_CLASSES_ROOT\vlc\shell\open\command /ve /t REG_SZ /d "python -c """import subprocess;subprocess.Popen(['mpv', '%%1'[6:]])"""" /f
