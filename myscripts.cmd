@ECHO OFF

CD /d "%~dp0"
@REM CHCP 65001

CALL install\install_choco.cmd
CALL install\install_autohotkey.cmd

ECHO Find python executable...
CALL install\find_python.cmd
IF NOT %errorlevel%==0 (
    CALL install\install_python.cmd
)

TITLE MyTerminal

IF NOT EXIST "%USERPROFILE%\.venv\myscripts" (
  python -m venv "%USERPROFILE%\.venv\myscripts" --system-site-packages
)
CALL "%USERPROFILE%\.venv\myscripts\Scripts\activate.bat"

ECHO Install python packages...
pip --disable-pip-version-check install -r requirements.txt >NUL

:main
python myscripts.py %*
IF errorlevel 1 GOTO main
