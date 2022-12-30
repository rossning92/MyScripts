@echo off
cd /d "%~dp0"
chcp 65001

call install\install_choco.cmd
call install\install_autohotkey.cmd

:: Find python executable
call install\find_python.cmd
if not %errorlevel%==0 (
    call install\install_python.cmd
)

:: Install python modules
python -m pip install --user -r requirement.txt

title MyScriptsTerminal

:main
python run.py %*
if errorlevel 1 goto main
