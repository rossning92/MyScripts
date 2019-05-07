@echo off

taskkill /f /im {{UE4_PROJECT_NAME}}* 2>nul

set BUILD_CONFIG=Development
:: set BUILD_CONFIG=Debug


call ..\_msbuild.cmd "{{UE_SOURCE}}\UE4.sln" /t:Games\{{UE4_PROJECT_NAME}} /p:Configuration="%BUILD_CONFIG%" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%


exit /b 0


:: call "{{UE_SOURCE}}\Engine\Build\BatchFiles\Build.bat" "{{UE4_PROJECT_NAME}}" Win64 %BUILD_CONFIG% -waitmutex-2017