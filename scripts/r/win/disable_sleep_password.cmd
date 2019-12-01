@echo off
set "KEY_NAME=HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Power\PowerSettings\0e796bdb-100d-47d6-a2d5-f7d2daa51f51"
reg add "%KEY_NAME%" /v DCSettingIndex /t REG_DWORD /d 0 /f
reg add "%KEY_NAME%" /v ACSettingIndex /t REG_DWORD /d 0 /f