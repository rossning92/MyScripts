@echo off

set CMDLINE=powershell.exe -NoProfile -InputFormat None -ExecutionPolicy Bypass %~dp0install_packages.ps1 

:: cscript %CMDLINE%

%~dp0..\bin\Elevate.exe -wait %CMDLINE%