# https://docs.lizardbyte.dev/projects/sunshine/en/latest/about/setup.html

set -e
cd ~

wget https://github.com/LizardByte/Sunshine/releases/latest/download/sunshine.pkg.tar.zst
sudo pacman -U --noconfirm sunshine.pkg.tar.zst

# Create and reload udev rules for uinput.
echo 'KERNEL=="uinput", SUBSYSTEM=="misc", OPTIONS+="static_node=uinput", TAG+="uaccess"' |
    sudo tee /etc/udev/rules.d/60-sunshine.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo modprobe uinput

# Enable permissions for KMS capture.
sudo setcap cap_sys_admin+p $(readlink -f $(which sunshine))

systemctl --user start sunshine
