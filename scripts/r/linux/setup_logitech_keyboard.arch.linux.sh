set -e

sudo pacman -S --noconfirm --needed solaar

sudo tee /usr/local/bin/disable_logitech_fn_keys.sh <<'EOF'
#!/usr/bin/bash
solaar config K380 fn-swap off &
solaar config K600 fn-swap off &
wait
EOF
sudo chmod +x /usr/local/bin/disable_logitech_fn_keys.sh

sudo tee /etc/udev/rules.d/42-logitech-keyboard.rules <<'EOF'
SUBSYSTEM=="bluetooth", ACTION=="add", KERNEL=="hci0:*", RUN+="/usr/local/bin/disable_logitech_fn_keys.sh"
EOF

sudo tee /etc/udev/rules.d/99-hidraw.rules <<'EOF'
KERNEL=="hidraw*", SUBSYSTEM=="hidraw", MODE="0664", GROUP="plugdev"
EOF

sudo udevadm control --reload
