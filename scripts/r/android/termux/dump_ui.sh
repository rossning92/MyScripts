#!/bin/bash
echo "Dumping UI..."
bash "$HOME/MyScripts/bin/run_script" r/android/dump_ui.py
am start --user 0 -n com.termux/.app.TermuxActivity >/dev/null 2>&1
read -n 1 -s -r -p "Press any key to continue..."
echo
