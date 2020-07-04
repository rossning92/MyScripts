@echo off
powershell -command "Rename-Computer -NewName ross-desktop"
run_script /r/install_fonts_zh_cn
run_script /r/win/customize_windows
