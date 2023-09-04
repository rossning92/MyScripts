# https://wiki.archlinux.org/title/Uncomplicated_Firewall

set -e
sudo pacman -S ufw

sudo ufw enable
sudo ufw status verbose
