set -e

sudo pacman -Syu --noconfirm

run_script r/linux/arch/install_yay.sh

yay -Syu --noconfirm
