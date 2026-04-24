# Autostart on any Linux desktop
mkdir -p ~/.config/autostart/
cat >~/.config/autostart/myscripts.desktop <<EOF
[Desktop Entry]
Type=Application
Name=myscripts
Exec=alacritty -e $HOME/myscripts/myscripts --startup
StartupNotify=false
Terminal=false
EOF
