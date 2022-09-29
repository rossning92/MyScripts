@echo off
setlocal enableextensions enabledelayedexpansion

:: strip double quotes from the "%1" argument if present, just in case (it'll be added later)
set "file=%~1"
:: convert backslashes into forward slashes, so 'echo loadfile' doesn't need escaped backslashes
set "file=%file:\=/%"
set cli_args=%*
set mpv_args=!cli_args:%1=!

tasklist /fi "imagename eq mpv.exe" 2>nul | findstr /i "mpv.exe" >nul
if %errorlevel% equ 0 (
    goto :IS_RUNNING
) else (
    start "" mpv.exe --input-ipc-server=mpv-socket %mpv_args% "%file%"
    goto :END
)

:IS_RUNNING
echo loadfile "%file%">\\.\pipe\mpv-socket
echo set pause no>\\.\pipe\mpv-socket
echo set window-minimized no>\\.\pipe\mpv-socket
echo show-progress>\\.\pipe\mpv-socket

:END
endlocal