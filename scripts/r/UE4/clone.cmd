@echo off

set "DIR={{UE_SOURCE}}"

md "%DIR%" 2>nul
cd /d "%DIR%"

git clone -b 4.21 --single-branch https://github.com/Oculus-VR/UnrealEngine.git --depth 1