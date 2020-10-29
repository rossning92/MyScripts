@echo off

setlocal

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

echo Cannot find MSBuild.exe
exit /b 1

:exec
REM start "msbuild low pri" /low /wait %MSBUILD% %*
%MSBUILD% %*
if not %errorlevel%==0 exit /b 1

exit /b 0
