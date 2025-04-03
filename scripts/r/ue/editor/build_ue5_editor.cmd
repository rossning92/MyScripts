@REM https://docs.unrealengine.com/5.0/en-US/Welcome/
@REM https://github.com/Oculus-VR/UnrealEngine

@echo off

cd /d "%UE_SOURCE%"

run_script r/ue/editor/SelectNoRegisterUEFileTypes.ahk

echo Killing running instances...
taskkill /t /f /im UE5Editor.exe
taskkill /t /f /im MSBuild.exe
taskkill /t /f /im FBuild.exe
taskkill /f /im cl.exe
taskkill /f /im Link.exe

if "%_CLEAN_BUILD%"=="1" (
    git clean -f -x -d
)

if not exist "UE5.sln" (
    echo Running Setup.bat
    cmd /c Setup.bat

    echo Running GenerateProjectFiles.bat
    cmd /c GenerateProjectFiles.bat
)

taskkill /f /im UE5Editor.exe 2>nul

@REM Install build dependencies:
@REM https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022
@REM "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" modify --installPath "C:\Program Files\Microsoft Visual Studio\2022\Community" --add Microsoft.VisualStudio.Workload.ManagedDesktop --add Microsoft.VisualStudio.Workload.NativeDesktop --config "%UE_SOURCE%\.vsconfig" --focusedUI --force --includeRecommended

run_script r/win/msbuild.cmd "UE5.sln" /t:Engine\UE5 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

@REM For building lighting:
@REM call _msbuild "UE5.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
@REM if %errorlevel% neq 0 exit /b %errorlevel%
