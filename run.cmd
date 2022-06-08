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
pip install -r requirement.txt

title my_scripts_console

:main
python main_console.py
if errorlevel 1 goto main
