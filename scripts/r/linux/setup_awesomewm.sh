set -e

# Install required packages
if [[ -f "/etc/debian_version" ]]; then
    packages="awesome xbacklight alsa-utils"
    for package in $packages; do
        dpkg -s "$package" >/dev/null 2>&1 || {
            sudo apt-get update
            sudo apt-get install -y "$package"
        }
    done
elif [[ -f "/etc/arch-release" ]]; then
    sudo pacman -S --noconfirm awesome xorg-server xorg-xinit awesome 
fi 

# Copy awesome config file
ln -sf "$(dirname "$0")/../../../settings/awesome" $HOME/.config/
