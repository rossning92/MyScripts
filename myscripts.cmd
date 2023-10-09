@ECHO OFF

CD /d "%~dp0"
CHCP 65001

CALL install\install_choco.cmd
CALL install\install_autohotkey.cmd

ECHO Find python executable...
CALL install\find_python.cmd
IF NOT %errorlevel%==0 (
    CALL install\install_python.cmd
)

TITLE MyScriptsTerminal

IF NOT EXIST .venv\ (
  python -m venv .venv --system-site-packages
)
CALL .venv\Scripts\activate.bat

ECHO Install python packages...
python -m pip install --user -r requirements.txt >NUL

:main
python myscripts.py %*
IF errorlevel 1 GOTO main

