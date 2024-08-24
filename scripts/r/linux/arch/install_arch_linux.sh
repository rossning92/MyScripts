# https://wiki.archlinux.org/title/Installation_guide

set -e

mkdir -p ~/Downloads
cd ~/Downloads

# https://wiki.archlinux.org/title/Installation_guide#Acquire_an_installation_image
if [ ! -f "archlinux-x86_64.iso" ]; then
    curl -O https://geo.mirror.pkgbuild.com/iso/latest/archlinux-x86_64.iso
fi

# Connect to Wi-Fi
# 1. iwctl
# 2. station wlan0 scan
# 3. station wlan0 connect <SSID>

# Run archinstall
