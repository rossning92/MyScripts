@echo off

cd /d "%~dp0"

set QTDIR=
set QT_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=
set QML_IMPORT_PATH=
set QML2_IMPORT_PATH=


set CONDA_PATH=

:: Anaconda3 prefered
set PATH=%LOCALAPPDATA%\Continuum\anaconda3;%USERPROFILE%\anaconda3;C:\tools\miniconda3;C:\Python36;%LOCALAPPDATA%\Programs\Python\Python36;%PATH%

:: Install required packages
where python
if not %errorlevel%==0 (
	call install\install_all_elivated.cmd
)

:: Install python modules
pip install -r requirement.txt

start "MyScripts - Console" python autoreload.py