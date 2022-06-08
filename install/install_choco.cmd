@echo off
where choco >nul
if %errorlevel% neq 0 powershell Start-Process powershell -verb runAs -wait -ArgumentList `-NoProfile,`-InputFormat,None,`-ExecutionPolicy,Bypass,`-Command,iex` `(`(New-Object` System.Net.WebClient`).DownloadString`(`'https://chocolatey.org/install.ps1`'`)`)
