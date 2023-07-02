set -e

if [[ "$(uname -r)" != *"-surface"* ]]; then
    # https://github.com/linux-surface/linux-surface/wiki/Installation-and-Setup#manually-installing-the-repository
    wget -qO - https://raw.githubusercontent.com/linux-surface/linux-surface/master/pkg/keys/surface.asc |
        gpg --dearmor | sudo dd of=/etc/apt/trusted.gpg.d/linux-surface.gpg
    echo "deb [arch=amd64] https://pkg.surfacelinux.com/debian release main" |
        sudo tee /etc/apt/sources.list.d/linux-surface.list
    sudo apt update
    sudo apt install linux-image-surface linux-headers-surface libwacom-surface iptsd
    # sudo apt install linux-surface-secureboot-mok -y
    sudo update-grub
fi

# Config thermald
# https://github.com/linux-surface/linux-surface/tree/master/contrib/thermald
echo 'Configure thermald...'
sudo cp "$(dirname "$0")/../../../settings/linux-surface/thermal-conf.xml" /etc/thermald/thermal-conf.xml
sudo systemctl restart thermald.service
sudo systemctl status thermald.service
