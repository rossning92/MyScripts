@echo off

set "DIR={{UE_SOURCE}}"

md "%DIR%" 2>nul
cd /d "%DIR%"

REM git clone -b 4.22 --single-branch https://github.com/Oculus-VR/UnrealEngine.git --depth 1 .

git clone -b 4.22 --single-branch https://github.com/EpicGames/UnrealEngine.git --depth 1 .
