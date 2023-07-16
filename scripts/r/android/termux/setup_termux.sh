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

# Install required packages
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
