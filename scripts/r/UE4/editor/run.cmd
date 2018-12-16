@echo off
setlocal


set DATA_CACHE_DIR=C:\UE4-DataCache
set BIN_DIR={{UE_SOURCE}}\Engine\Binaries\Win64\


taskkill /f /im UE4Editor.exe 2>nul


cd /d "%BIN_DIR%"

if 1==2 (
    md %DATA_CACHE_DIR% 2>nul
    set UE-SharedDataCachePath=%DATA_CACHE_DIR%
    start UE4Editor.exe -ddc=noshared
) else (
    start UE4Editor.exe
)