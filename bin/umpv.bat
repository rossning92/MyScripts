@ECHO OFF
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: strip double quotes from the "%1" argument if present, just in case (it'll be added later)
SET "file=%~1"
:: convert backslashes into forward slashes, so 'echo loadfile' doesn't need escaped backslashes
SET "file=%file:\=/%"
SET cli_args=%*
SET mpv_args=!cli_args:%1=!

TASKLIST /FI "IMAGENAME eq mpv.exe" 2>NUL | FINDSTR /i "mpv.exe" >NUL
IF %errorlevel% EQU 0 ( GOTO :IS_RUNNING ) ELSE (
    START "" mpv.exe --input-ipc-server=mpv-socket %mpv_args% "%file%"
    GOTO :END
)

:IS_RUNNING
echo loadfile "%file%">\\.\pipe\mpv-socket
echo set pause no>\\.\pipe\mpv-socket

:END
endlocal