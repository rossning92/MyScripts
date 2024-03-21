uname -r

# Latest stable kernel
sudo pacman -S --noconfirm linux

# Re-generate the GRUB configuration file
sudo grub-mkconfig -o /boot/grub/grub.cfg
