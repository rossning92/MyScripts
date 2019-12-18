@echo off

call "C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\Common7\Tools\VsDevCmd.bat" -no_logo
if %errorlevel%==0 goto success

call "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\Common7\Tools\VsDevCmd.bat" -no_logo
if %errorlevel%==0 goto success

echo Cannnot locate Visual Studio 
goto :eof

:success
clrver
cd /d "%~dp1"
csc -nologo "%~nx1"
if not %errorlevel%==0 goto :eof

"%~n1.exe"