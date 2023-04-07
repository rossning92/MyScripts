@REM https://docs.unrealengine.com/5.0/en-US/Welcome/

@echo off

cd /d "%UE_SOURCE%"

if not exist "UE5.sln" (
    Setup.bat
    GenerateProjectFiles.bat
)

if not exist "Engine\Plugins\Runtime\OculusXR" (
    git submodule update --init --recursive
)

taskkill /f /im UE5Editor.exe 2>nul

@REM for building UnrealBuildTool
@REM choco install -y -s https://chocolatey.org/api/v2/ dotnet-6.0-sdk
@REM choco install -y -s https://chocolatey.org/api/v2/ dotnetcore-sdk
@REM
@REM Alternative:
@REM "C:\Program Files (x86)\Microsoft Visual Studio\Installer\vs_installer.exe" modify --installPath "C:\Program Files (x86)\Microsoft Visual Studio\2019\Community" --add "Microsoft.VisualStudio.Workload.ManagedDesktop" --focusedUI --force
@REM https://docs.microsoft.com/en-us/visualstudio/install/use-command-line-parameters-to-install-visual-studio?view=vs-2022

run_script r/win/msbuild.cmd "UE5.sln" /t:Engine\UE5 /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
if %errorlevel% neq 0 exit /b %errorlevel%

:: For build lighting
@REM call _msbuild "UE5.sln" /t:Programs\UnrealLightmass /p:Configuration="Development Editor" /p:Platform=Win64 /maxcpucount /nologo
@REM if %errorlevel% neq 0 exit /b %errorlevel%
