set -e
sudo pacman -S reflector --noconfirm
sudo reflector --verbose --protocol https -n 10 -l 150 --sort rate --thread 300 --save /etc/pacman.d/mirrorlist
