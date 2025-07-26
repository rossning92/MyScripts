# https://itsfoss.com/switch-kernels-arch-linux/
set -e

yay -S --noconfirm --needed grub

sudo sed -i -E 's/^#?GRUB_DISABLE_SUBMENU=.*/GRUB_DISABLE_SUBMENU=y/' /etc/default/grub
sudo sed -i -E 's/^#?GRUB_DEFAULT=.*/GRUB_DEFAULT=saved/' /etc/default/grub
sudo sed -i -E 's/^#?GRUB_SAVEDEFAULT=.*/GRUB_SAVEDEFAULT=true/' /etc/default/grub

sudo grub-mkconfig -o /boot/grub/grub.cfg
