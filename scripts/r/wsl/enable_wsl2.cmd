REM https://docs.microsoft.com/en-us/windows/wsl/install-win10#update-to-wsl-2

dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

powershell -Command "Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart"

REM  Step 4 - Download the Linux kernel update package

wsl --set-default-version 2
