set -e
set -x

(
    mkdir -p ~/Downloads
    cd ~/Downloads

    # Download and install termux
    apk="https://github.com/termux/termux-app/releases/download/v0.118.0/termux-app_v0.118.0+github-debug_arm64-v8a.apk"
    name="$(basename "$apk")"
    if [[ ! -f "$name" ]]; then
        echo "Download $apk..."
        curl -o "$name" -OL "$apk"
    fi
    run_script r/android/install_apk.py "$name"
)

(
    cd "$(dirname "$0")"
    adb push setup_termux.sh /data/local/tmp/setup_termux.sh

    # adb shell dumpsys package com.termux | grep userId=

    adb shell am start -n com.termux/.app.TermuxActivity
    echo 'Wait for 5 seconds.'
    sleep 5
    adb shell input text "bash\ /data/local/tmp/setup_termux.sh"
    adb shell input keyevent 113 && adb shell input keyevent 66
)
