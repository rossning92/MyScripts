@ECHO OFF

cd /d "%~dp0"
chcp 65001

CALL install\install_choco.cmd
CALL install\install_autohotkey.cmd

@REM Find python executable
CALL install\find_python.cmd
if not %errorlevel%==0 (
    CALL install\install_python.cmd
)

@REM Install python modules
python -m pip install --user -r requirements.txt

TITLE MyScriptsTerminal

:main
python myscripts.py %*
IF errorlevel 1 GOTO main

