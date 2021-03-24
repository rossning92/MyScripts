$ProgressPreference = 'SilentlyContinue'

Invoke-WebRequest -Uri "https://github.com/Lexikos/AutoHotkey_L/releases/download/v1.1.32.00/AutoHotkey_1.1.32.00_setup.exe" -OutFile "$env:TEMP\AutoHotkey_setup.exe"

& "$env:TEMP\AutoHotkey_setup.exe" /S /uiAccess=1
