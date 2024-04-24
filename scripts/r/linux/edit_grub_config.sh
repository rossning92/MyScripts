# https://itsfoss.com/switch-kernels-arch-linux/
set -e

sudo pacman -S --noconfirm --needed grub

sudo nvim /etc/default/grub

sudo grub-mkconfig -o /boot/grub/grub.cfg
