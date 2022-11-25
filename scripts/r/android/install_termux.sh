cd ~/Downloads
set -e

# curl -o termux-app.apk -OL https://f-droid.org/repo/com.termux_118.apk
# run_script r/android/install_apk.py "termux-app.apk"

curl -o termux-boot.apk -OL https://f-droid.org/repo/com.termux.boot_7.apk
run_script r/android/install_apk.py "termux-boot.apk"

cat >setup_termux.sh <<_EOF_
pkg update
pkg install openssh -y
ssh-keygen -A
echo -e "123456\n123456" | passwd
sshd

cat >~/.bashrc <<EOF
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sshd
EOF

mkdir -p >~/.termux/boot/
cat >~/.termux/boot/start-sshd <<EOF
#!/data/data/com.termux/files/usr/bin/sh
termux-wake-lock
sshd -D
chmod 755 ~/.termux/boot/start-sshd
EOF

am start -n com.termux.boot/.BootActivity
_EOF_
uid=$(adb shell stat -c %u /data/data/com.termux)
adb push setup_termux.sh /data/local/tmp/setup_termux.sh

adb shell am start -n com.termux/.app.TermuxActivity
adb shell input text "bash\ /data/local/tmp/setup_termux.sh"
adb shell input keyevent 113 && adb shell input keyevent 66
