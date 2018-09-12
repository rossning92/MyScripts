@echo off

cscript runas.vbs powershell.exe -NoProfile -InputFormat None -ExecutionPolicy Bypass %~dp0install_packages.ps1