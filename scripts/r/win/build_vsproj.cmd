@echo off

setlocal

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

set MSBUILD="C:\Program Files (x86)\Microsoft Visual Studio\2017\Professional\MSBuild\15.0\Bin\MSBuild.exe"
if exist %MSBUILD% goto exec

echo Cannot find MSBuild.exe
exit /b 1

:exec
%MSBUILD% %*
if not %errorlevel%==0 exit /b 1
exit /b 0

@REM TODO: change to something more general
call "%~dp0_msbuild.cmd" "UE4.sln" /t:Engine\UE4 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
