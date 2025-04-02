@echo off
setlocal enabledelayedexpansion

set "MSBUILD=C:\Program Files\Microsoft Visual Studio\2022\Community\MSBuild\Current\Bin\MSBuild.exe"
if not exist "!MSBUILD!" (
  set "MSBUILD=C:\Program Files (x86)\Microsoft Visual Studio\2019\Community\MSBuild\Current\Bin\MSBuild.exe"
  if not exist "!MSBUILD!" (
    set "MSBUILD=C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\MSBuild\15.0\Bin\MSBuild.exe"
    if not exist "!MSBUILD!" (
        echo Cannot find MSBuild.exe
        exit /b 1
    )
  )
)

echo MSBuild Path: %MSBUILD%
"%MSBUILD%" %* /maxcpucount /nologo
if not %errorlevel%==0 exit /b 1
exit /b 0