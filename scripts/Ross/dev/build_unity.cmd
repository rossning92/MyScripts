@echo off

set UNITY="C:\Program Files\Unity\Editor\Unity.exe"
set UNITY_PROJECT_PATH="C:\Users\Ross\Documents\Unity\TestProject"
set UNITY_OUTPUT_EXE="C:\Temp\TestProject\TestProject.exe"
set UNITY_LOG="%LOCALAPPDATA%\Unity\Editor\Editor.log"


taskkill /f /im Unity.exe 2>nul

del /s /q %UNITY_LOG%
start /wait "" %UNITY% -batchmode -projectPath %UNITY_PROJECT_PATH% -buildWindows64Player %UNITY_OUTPUT_EXE% -quit

echo Return Code: %errorlevel%
if not %errorlevel%==0 (
	start %UNITY_LOG%
)