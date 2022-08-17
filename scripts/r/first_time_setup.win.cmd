@echo off

run_script @cd=1 r/win/config_my_windows.cmd
run_script @cd=1 r/win/add_cn_lang.ps1
run_script @cd=1 r/dev/choco/install_package.py @ross
run_script @cd=1 r/vscode/config_vscode.py
run_script @cd=1 r/android/install_android_sdk.py
