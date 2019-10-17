@echo off

taskkill /f /im UE4Editor.exe 2>nul

call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Engine\UE4 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: For build lighting
call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: For viewing profiling data
:: call _msbuild "{{UE_SOURCE}}\UE4.sln" /t:Programs\UnrealFrontend /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
:: if %errorlevel% neq 0 exit /b %errorlevel%

exit /b 0





REM ================================================================
:: Build UE4Editor
call "{{UE_SOURCE}}\Engine\Build\BatchFiles\Build.bat" UE4Editor Win64 Development -WaitMutex -FromMsBuild
if not %errorlevel%==0 exit /b 1

:: Build ShaderCompileWorker
call "{{UE_SOURCE}}\Engine\Build\BatchFiles\Build.bat" ShaderCompileWorker Win64 Development -waitmutex-2017
if not %errorlevel%==0 exit /b 1

exit /b 0



REM ================================================================
:: OLD BUILD LOGIC

set MSBUILD_PARAMS=/p:Platform=x64 /maxcpucount /nologo

call msbuild %MSBUILD_PARAMS% /p:Configuration=Development_Editor "{{UE_SOURCE}}\Engine\Intermediate\ProjectFiles\UE4.vcxproj"
if not %errorlevel%==0 exit /b 1

call msbuild %MSBUILD_PARAMS% /p:Configuration=Development_Program "{{UE_SOURCE}}\Engine\Intermediate\ProjectFiles\ShaderCompileWorker.vcxproj"
if not %errorlevel%==0 exit /b 1