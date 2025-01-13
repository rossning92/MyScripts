@echo off

run_script r/wsl/enable_wsl1.ps1

wsl --set-default-version 1

run_script r/wsl/install_distro_ubuntu.ps1
pause

run_script r/wsl/setup_wsl.sh