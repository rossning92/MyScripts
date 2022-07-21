@echo off

cd /d "%UE_SOURCE%\Engine"

echo "Killing running instances..."
taskkill /f /t /im UnrealBuildTool.exe
taskkill /t /f /im UE4Editor.exe
taskkill /t /f /im MSBuild.exe
taskkill /t /f /im FBuild.exe
taskkill /f /im cl.exe
taskkill /f /im Link.exe

rd /s /q Build
rd /s /q Intermediate
rd /s /q DerivedDataCache
rd /s /q Saved
