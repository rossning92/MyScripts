@echo off

if "%~1"=="" (
    echo First parameter must be a full path to a file. Exiting with error.
    exit /b 1
)

echo "%1" | find ":\" >nul || (
    echo Parameter must be a full path to a file.
    exit /b 1
)

cd "%~dp1"

C:\ProgramData\chocolatey\tools\shimgen.exe --path=%~nx1 -o C:\MyScripts\bin\%~n1.exe