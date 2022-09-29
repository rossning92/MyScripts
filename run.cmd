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

title MyScripts - Console

:main
python main_console.py
if errorlevel 1 goto main
