set -e
mkdir -p ~/Downloads
cd ~/Downloads

# Download and install termux apks
declare -a apks=(
    "https://f-droid.org/repo/com.termux_118.apk"
    "https://f-droid.org/repo/com.termux.boot_7.apk"
)
for apk in "${apks[@]}"; do
    name="$(basename "$apk")"
    if [ ! -f "$name" ]; then
        curl -o "$name" -OL "$apk"
    fi
    run_script r/android/install_apk.py "$name"
done

cat >setup_termux.sh <<'_EOF_'

# Install ssh server
pkg install openssh -y
ssh-keygen -A
echo -e "123456\n123456" | passwd
sshd

# Configure .bashrc
cat >~/.bashrc <<EOF
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sshd
EOF

# Configure startup
mkdir -p ~/.termux/boot/
cat >~/.termux/boot/start-sshd <<EOF
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sshd -D
chmod 755 ~/.termux/boot/start-sshd
EOF

# am start -n com.termux.boot/.BootActivity

{{ include('r/android/termux/install_ssh_server.sh') }}
_EOF_
adb push setup_termux.sh /data/local/tmp/setup_termux.sh

adb shell dumpsys package com.termux | grep userId=

adb shell am start -n com.termux/.app.TermuxActivity
echo 'Wait for 5 seconds.'
sleep 5
adb shell input text "bash\ /data/local/tmp/setup_termux.sh"
adb shell input keyevent 113 && adb shell input keyevent 66
