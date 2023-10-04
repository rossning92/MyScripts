set -e

if [[ ! -f "/etc/arch-release" ]]; then
    echo 'ERROR: must run this script on arch-based distro.'
    exit 1
fi

# Install surface linux kernel
if [[ "$(uname -r)" != *"-surface"* ]]; then

    # https://github.com/linux-surface/linux-surface/wiki/Installation-and-Setup#Arch
    curl -s https://raw.githubusercontent.com/linux-surface/linux-surface/master/pkg/keys/surface.asc |
        sudo pacman-key --add -
    sudo pacman-key --finger 56C464BAAC421453
    sudo pacman-key --lsign-key 56C464BAAC421453

    repo_entry="[linux-surface]
Server = https://pkg.surfacelinux.com/arch/"

    if ! grep -qF "$repo_entry" /etc/pacman.conf; then
        # Add the repository entry to the end of the file
        echo "$repo_entry" | sudo tee -a /etc/pacman.conf >/dev/null
        echo "Repository added successfully."
    else
        echo "Repository entry already exists."
    fi

    sudo pacman -Syu --noconfirm
    sudo pacman -S linux-surface linux-surface-headers iptsd --noconfirm

    sudo grub-mkconfig -o /boot/grub/grub.cfg
fi

# Config thermald
# https://github.com/linux-surface/linux-surface/tree/master/contrib/thermald
echo 'Setup thermald...'
sudo pacman -S thermald --noconfirm
sudo cp "$(dirname "$0")/../../../settings/linux-surface/thermal-conf.xml" /etc/thermald/thermal-conf.xml
sudo systemctl enable thermald.service --now

# Brightness control
if command -v apt &>/dev/null; then
    sudo apt install light -y
else
    sudo pacman -S light --noconfirm
fi
sudo usermod -aG video $(whoami)
sudo tee /etc/udev/rules.d/90-brightnessctl.rules <<-EOF
ACTION=="add", SUBSYSTEM=="backlight", RUN+="/bin/chgrp video /sys/class/backlight/%k/brightness"
ACTION=="add", SUBSYSTEM=="backlight", RUN+="/bin/chmod g+w /sys/class/backlight/%k/brightness"
ACTION=="add", SUBSYSTEM=="leds", RUN+="/bin/chgrp input /sys/class/leds/%k/brightness"
ACTION=="add", SUBSYSTEM=="leds", RUN+="/bin/chmod g+w /sys/class/leds/%k/brightness"
EOF

# Camera support
# https://github.com/linux-surface/linux-surface/wiki/Camera-Support
sudo pacman -S libcamera --noconfirm
