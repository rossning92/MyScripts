@echo off
powershell -command "Rename-Computer -NewName Ross-Desktop"
run_script /r/install_fonts_zh_cn
run_script /r/win/customize_windows
