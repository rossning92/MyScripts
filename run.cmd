set QTDIR=
set QT_PLUGIN_PATH=
set QT_QPA_PLATFORM_PLUGIN_PATH=
set QML_IMPORT_PATH=
set QML2_IMPORT_PATH=
::set PATH=%LOCALAPPDATA%\Programs\Python\Python36;%PATH%

start "MyScripts - Console" python autoreload.py

cd ahk
start AutoHotkeyU64 hotkeys.ahk