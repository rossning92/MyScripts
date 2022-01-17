@echo off

if not exist "{{UE_SOURCE}}\UE4.sln" (
    run_script setup.py
)

echo "Killing running instances..."
taskkill /t /f /im UE4Editor.exe
taskkill /t /f /im MSBuild.exe
taskkill /t /f /im FBuild.exe
taskkill /f /im cl.exe
taskkill /f /im Link.exe

call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Engine\UE4 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: UnrealLightmass: light build tool
call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: UnrealFrontend: profiling tool
:: call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Programs\UnrealFrontend /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
:: if %errorlevel% neq 0 exit /b %errorlevel%

exit /b 0





REM ================================================================
:: Build UE4Editor
call "Engine\Build\BatchFiles\Build.bat" UE4Editor Win64 Development -WaitMutex -FromMsBuild
if not %errorlevel%==0 exit /b 1

:: Build ShaderCompileWorker
call "Engine\Build\BatchFiles\Build.bat" ShaderCompileWorker Win64 Development -waitmutex-2017
if not %errorlevel%==0 exit /b 1

exit /b 0
