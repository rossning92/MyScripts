set -e
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

cat >setup_termux.sh <<'_EOF_'
set -e
export DEFAULT_ALWAYS_YES=true
export ASSUME_ALWAYS_YES=true

pkg up -y

# Install git
pkg install git -y

# Configure .bashrc
cat >~/.bashrc <<EOF
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
EOF

{{ include('r/android/termux/install_ssh_server.sh') }}
_EOF_
adb push setup_termux.sh /data/local/tmp/setup_termux.sh

adb shell dumpsys package com.termux | grep userId=

adb shell am start -n com.termux/.app.TermuxActivity
echo 'Wait for 5 seconds.'
sleep 5
adb shell input text "bash\ /data/local/tmp/setup_termux.sh"
adb shell input keyevent 113 && adb shell input keyevent 66
