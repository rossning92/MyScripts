# https://wiki.archlinux.org/title/CUPS

set -e
sudo pacman -S --noconfirm cups
yay -S --noconfirm brother-hll2460dw # Brother HL-L2460DW Printer Driver
# Configure through the web interface: http://localhost:631/
