@REM https://docs.unrealengine.com/5.0/en-US/Welcome/

@echo off

cd /d "%UE_SOURCE%"

run_script r/UE4/editor/SelectNoRegisterUEFileTypes.ahk

echo Killing running instances...
taskkill /t /f /im UE5Editor.exe
taskkill /t /f /im MSBuild.exe
taskkill /t /f /im FBuild.exe
taskkill /f /im cl.exe
taskkill /f /im Link.exe

if "%_CLEAN_BUILD%"=="1" (
    @REM del UE5.sln
    git clean -f -x -d
)

if not exist "UE5.sln" (
    copy "C:\Users\rossning92\Downloads\Commit.gitdeps.xml" "C:\Projects\ue5-ovr-internal\Engine\Build\Commit.gitdeps.xml" /y
    cmd /c Setup.bat
    cmd /c GenerateProjectFiles.bat
)

if not exist "Engine\Plugins\Runtime\OculusXR" (
    git submodule update --init --recursive
)

taskkill /f /im UE5Editor.exe 2>nul

@REM Alternative:
@REM "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vs_installer.exe" modify --installPath "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community" --add "Microsoft.VisualStudio.Workload.ManagedDesktop" --focusedUI --force
@REM https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022

run_script r/win/msbuild.cmd "UE5.sln" /t:Engine\UE5 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: For build lighting
@REM call _msbuild "UE5.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
@REM if %errorlevel% neq 0 exit /b %errorlevel%
