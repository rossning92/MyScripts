# Key mapping using https://github.com/rvaiya/keyd
# Map "CapsLock" to "Control + Meta" key.

yay -S --noconfirm --needed --needed keyd

sudo tee /etc/keyd/default.conf <<EOF
[ids]
*
[main]
rightcontrol = rightcontrol
capslock = overload(capslock, esc)

[capslock:C-M]
EOF

sudo systemctl restart keyd.service --now
