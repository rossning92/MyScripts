# Autostart on any Linux desktop
mkdir -p ~/.config/autostart/
cat >~/.config/autostart/myscripts.desktop <<EOF
[Desktop Entry]
Type=Application
Name=MyScripts
Exec=alacritty -e $HOME/MyScripts/myscripts --startup
StartupNotify=false
Terminal=false
EOF
