set -e
sudo pacman -S --noconfirm libvirt virt-manager qemu-full dnsmasq dmidecode
sudo systemctl enable --now libvirtd.service virtlogd.service

# Enable management of virtual machines without root
sudo usermod -aG libvirt $USER

# Enable automatic start of the default virtual network
sudo virsh net-autostart default
sudo virsh net-start default
