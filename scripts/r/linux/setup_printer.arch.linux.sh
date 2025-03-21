# https://wiki.archlinux.org/title/CUPS

set -e
sudo pacman -S --noconfirm cups ghostscript
sudo systemctl restart cups.service --now

# Configure through the web interface: http://localhost:631/
# Add a printer, e.g.: http://BRW4C82A9805513.local/ipp
