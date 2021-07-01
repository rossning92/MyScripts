@REM https://docs.unrealengine.com/5.0/en-US/Welcome/

@echo off

if not exist "{{UE_SOURCE}}\UE5.sln" (
    run_script setup.py
)

taskkill /f /im UE5Editor.exe 2>nul

set "MSBUILD=C:\Program Files (x86)\Microsoft Visual Studio\2019\Professional\MSBuild\Current\Bin\amd64\MSBuild.exe"
"%MSBUILD%" "{{UE_SOURCE}}\UE5.sln" /t:Engine\UE5 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: For build lighting
@REM call _msbuild "{{UE_SOURCE}}\UE5.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
@REM if %errorlevel% neq 0 exit /b %errorlevel%
