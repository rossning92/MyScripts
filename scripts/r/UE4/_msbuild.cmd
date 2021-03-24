@echo off

setlocal

set msbuild="C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
if exist %msbuild% goto exec

set msbuild="C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"
if exist %msbuild% goto exec

echo Cannot find MSBuild.exe
exit /b 1

:exec
%msbuild% %*
if not %errorlevel%==0 exit /b 1

exit /b 0