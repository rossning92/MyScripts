set -e

export DEFAULT_ALWAYS_YES=true
export ASSUME_ALWAYS_YES=true

pkg up -y

# ==============================
# Install packages
# ==============================
declare -a packages=("python" "git" "gh" "termux-api")
for package in "${packages[@]}"; do
    dpkg -s "$package" >/dev/null 2>&1 || {
        pkg update
        pkg install -y "$package"
    }
done

# Workaround for major performance degradation with most termux-api calls
# See https://github.com/termux/termux-api/issues/552
sed -i 's#^exec /system/bin/app_process /#exec /system/bin/app_process -Xnoimage-dex2oat /#' "$PREFIX/bin/am"

# ==============================
# Configure bashrc
# ==============================
cat >~/.bashrc <<EOF
#!/data/data/com.termux/files/usr/bin/sh
# termux-wake-lock
EOF

# ==============================
# Configure terminal color theme
# ==============================
cat >~/.termux/colors.properties <<EOF
# https://draculatheme.com/
# https://github.com/dracula/xresources/blob/master/Xresources
# special
foreground=#f8f8f2
cursor=#f8f8f2
background=#282a36
# black
color0=#000000
color8=#4d4d4d
# red
color1=#ff5555
color9=#ff6e67
# green
color2=#50fa7b
color10=#5af78e
# yellow
color3=#f1fa8c
color11=#f4f99d
# blue
color4=#caa9fa
color12=#caa9fa
# magenta
color5=#ff79c6
color13=#ff92d0
# cyan
color6=#8be9fd
color14=#9aedfe
# white
color7=#bfbfbf
color15=#e6e6e6
EOF

cat >~/.termux/termux.properties <<EOF
allow-external-apps = true
EOF

# ==============================
# Install SSH Server
# ==============================

# https://joeprevite.com/ssh-termux-from-computer/

pkill sshd || true

pkg install openssh -y

ssh-keygen -A
echo -e "123456\n123456" | passwd

sshd

# Check for SSH daemon logs
sleep 2
logcat -s 'sshd:*' -d | tail -n 10

# Run sshd at startup
if [[ ! -f ~/.bashrc ]] || ! grep -qF -- "sshd" ~/.bashrc; then
    echo "sshd" >>~/.bashrc
fi

# https://stackoverflow.com/questions/13322485/how-to-get-the-primary-ip-address-of-the-local-machine-on-linux-and-os-x
ipaddr=$(ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p')

echo "------"
echo "Please login using: \`ssh $(whoami)@$ipaddr -p 8022\` with password: 123456"
echo "------"
