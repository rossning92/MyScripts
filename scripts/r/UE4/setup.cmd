@echo off

cd /d "{{UE_SOURCE}}"
if %errorlevel% neq 0 exit /b %errorlevel%


call Setup.bat
if %errorlevel% neq 0 exit /b %errorlevel%
