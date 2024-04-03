@ECHO OFF

run_script r/wsl/enable_wsl1.ps1

run_script r/wsl/install_distro_ubuntu_2004.ps1
PAUSE

run_script r/wsl/setup_wsl.sh