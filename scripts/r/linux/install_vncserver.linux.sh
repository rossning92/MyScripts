# https://wiki.archlinux.org/title/x11vnc

set -e

if [[ ! -x "$(command -v x11vnc)" ]]; then
    if [[ -f "/etc/arch-release" ]]; then
        sudo pacman -S --noconfirm x11vnc
    fi
fi

# Setup VNC password
if [[ ! -f ~/.vnc/passwd ]]; then
    x11vnc -usepw -storepasswd
fi

# Create a systemd service to launch an x11vnc server
# https://wiki.archlinux.org/title/X11vnc#Run_x11vnc_%22system-wide%22_in_(GDM_and_GNOME_Shell)
sudo tee /etc/systemd/system/x11vnc.service <<-EOF
[Service]
User=$USER
ExecStart=
ExecStart=/usr/bin/x11vnc -many -no6 -rfbport 5900 -rfbauth $HOME/.vnc/passwd -auth $HOME/.Xauthority -display :0
Restart=on-failure
RestartSec=3

[Install]
WantedBy=graphical.target
EOF

# Run it now
sudo systemctl daemon-reload
sudo systemctl restart x11vnc.service --now
systemctl status x11vnc.service
# sudo journalctl -u x11vnc.service -f
