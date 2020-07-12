@echo off

cd /d "%~dp0"

set QTDIR=
set QT_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=
set QML_IMPORT_PATH=
set QML2_IMPORT_PATH=

:: Find python executable
call install\find_python.cmd
if not %errorlevel%==0 (
	call install\install_all_elevated.cmd
)

:: Install python modules
pip install -r requirement.txt

start "my_scripts_console" python autoreload.py