sudo apt update
sudo apt install xserver-xorg-input-synaptics -y

# disable all animations
kwriteconfig5 --file ~/.config/kwinrc --group Compositing --key Enabled false
