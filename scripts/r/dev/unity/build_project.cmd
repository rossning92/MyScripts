@echo off

set UNITY="C:\Program Files\Unity 2018.2.0b9\Editor\Unity.exe"
set UNITY_PROJECT_PATH="{{UNITY_PROJECT_PATH}}"
set UNITY_OUTPUT_EXE="{{UNITY_PROJECT_PATH}}\Build\Build.exe"
set UNITY_LOG="%LOCALAPPDATA%\Unity\Editor\Editor.log"


taskkill /f /im Unity.exe 2>nul

del /s /q %UNITY_LOG%
start /wait "" %UNITY% -batchmode -projectPath %UNITY_PROJECT_PATH% -buildWindows64Player %UNITY_OUTPUT_EXE% -quit

echo Return Code: %errorlevel%
if not %errorlevel%==0 (
	start %UNITY_LOG%
)