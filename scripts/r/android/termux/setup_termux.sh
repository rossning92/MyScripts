set -e

file_append() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        echo "$2" >>$1
    fi
}

export DEFAULT_ALWAYS_YES=true
export ASSUME_ALWAYS_YES=true

pkg up -y

# ==============================
# Install packages
# ==============================
declare -a packages=(
    "expect"
    "fzf"
    "gh"
    "git"
    "less"
    "python-numpy"
    "python"
    "rclone"
    "screen"
    "sed"
    "termux-api"
    "unzip"
    "vim"
    "which"
)
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

# Config vim
ln -f -s $HOME/MyScripts/settings/vim/.vimrc $HOME/.vimrc

# ==============================
# Others
# ==============================

# WORKAROUND for TERMUX__USER_ID error when using xdg-open
file_append ~/.bashrc "export TERMUX__USER_ID=$(whoami)"

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

file_append ~/.bashrc "sshd"

# https://stackoverflow.com/questions/13322485/how-to-get-the-primary-ip-address-of-the-local-machine-on-linux-and-os-x
ipaddr=$(ifconfig | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p')

echo "------"
echo "Please login using: \`ssh $(whoami)@$ipaddr -p 8022\` with password: 123456"
echo "------"
