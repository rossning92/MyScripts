@echo off

call "C:\Program Files (x86)\Microsoft Visual Studio\2017\BuildTools\Common7\Tools\VsDevCmd.bat" -no_logo
if %errorlevel%==0 goto success

call "C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\Tools\VsDevCmd.bat" -no_logo
if %errorlevel%==0 goto success

call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat" -no_logo
if %errorlevel%==0 goto success

echo Failed to locate Visual Studio...
pause >NUL
goto :eof

:success
clrver
cd /d "%~dp1"
csc -nologo "%~nx1"
if not %errorlevel%==0 goto :eof

"%~n1.exe"