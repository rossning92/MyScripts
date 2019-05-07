@echo off

cd /d "{{UE_SOURCE}}"


call GenerateProjectFiles.bat -2017
if not %errorlevel%==0 exit /b 1

::start UE4.sln