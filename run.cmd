@echo off

set QTDIR=
set QT_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=
set QML_IMPORT_PATH=
set QML2_IMPORT_PATH=


set CONDA_PATH=%LOCALAPPDATA%\Continuum\anaconda3

set PATH=%CONDA_PATH%;%CONDA_PATH%\Scripts;C:\Python36;C:\Python36\Scripts;%LOCALAPPDATA%\Programs\Python\Python36;%LOCALAPPDATA%\Programs\Python\Python36\Scripts;%PATH%

:: Install required packages
where python
if not %errorlevel%==0 (
	call install\install_all.cmd
)

:: Install python modules
pip install -r requirement.txt

start "MyScripts - Console" python autoreload.py