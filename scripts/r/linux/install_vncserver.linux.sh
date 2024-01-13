# https://wiki.archlinux.org/title/x11vnc

set -e

if [[ ! -x "$(command -v x11vnc)" ]]; then
    if [[ -f "/etc/arch-release" ]]; then
        sudo pacman -S --noconfirm x11vnc
    fi
fi

# Setup VNC password
if [[ ! -f ~/.vnc/passwd ]]; then
    vncpasswd
fi

# Create a systemd service to launch an x11vnc server
sudo tee /etc/systemd/system/x11vnc.service <<-EOF
[Service]
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
