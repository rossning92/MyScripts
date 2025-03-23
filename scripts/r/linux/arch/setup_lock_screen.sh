set -e

sudo pacman -S --noconfirm i3lock

cat <<EOF | sudo tee /usr/lib/systemd/system/betterlockscreen@.service
[Unit]
Description=Lock screen when going to sleep/suspend
Before=sleep.target
Before=suspend.target

[Service]
User=%I
Type=simple
Environment=DISPLAY=:0
ExecStart=/usr/bin/i3lock -n
TimeoutSec=infinity
ExecStartPost=/usr/bin/sleep 1

[Install]
WantedBy=sleep.target
WantedBy=suspend.target
EOF

sudo systemctl enable betterlockscreen@$(whoami)
