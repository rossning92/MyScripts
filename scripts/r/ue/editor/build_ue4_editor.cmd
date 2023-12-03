@echo off

cd /d "%UE_SOURCE%"

echo "Killing running instances..."
taskkill /t /f /im UE4Editor.exe
taskkill /t /f /im MSBuild.exe
taskkill /t /f /im FBuild.exe
taskkill /f /im cl.exe
taskkill /f /im Link.exe

if "%_CLEAN_BUILD%"=="1" (
    git clean -f -x -d
)

if not exist "UE4.sln" (
    run_script r/ue/editor/setup_env.py
)

call "%~dp0_msbuild.cmd" "UE4.sln" /t:Engine\UE4 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: UnrealLightmass: light build tool
call "%~dp0_msbuild.cmd" "UE4.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: UnrealFrontend: profiling tool
:: call _msbuild "UE4.sln" /t:Programs\UnrealFrontend /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
:: if %errorlevel% neq 0 exit /b %errorlevel%
