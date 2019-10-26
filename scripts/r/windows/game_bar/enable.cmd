@echo off

:: Enable
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 1 /f
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v GameDVR_Enabled /t REG_DWORD /d 1 /f

:: 60 fps
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v VideoEncodingFrameRateMode /t REG_DWORD /d 1 /f

:: Video quality: high
reg add "HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR" /v VideoEncodingBitrateMode /t REG_DWORD /d 1 /f