set -e

yay -S --noconfirm betterlockscreen

cat <<EOF | sudo tee /usr/lib/systemd/system/betterlockscreen@.service
[Unit]
Description=Lock screen when going to sleep/suspend
Before=sleep.target
Before=suspend.target

[Service]
User=%I
Type=forking
Environment=DISPLAY=:0
ExecStart=/usr/bin/betterlockscreen --lock
TimeoutSec=infinity
ExecStartPost=/usr/bin/sleep 1

[Install]
WantedBy=sleep.target
WantedBy=suspend.target
EOF

systemctl enable betterlockscreen@$USER --now
