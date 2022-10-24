@echo off
set "DEST=%USERPROFILE%\.vscode\extensions\videoedit"
if exist "%DEST%" (
    rd "%DEST%"
)
MKLINK /J "%DEST%" %~dp0_extension
