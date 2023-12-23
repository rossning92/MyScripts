set -e

prepend_if_not_exist() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        printf '%s\n%s\n' "$2" "$(cat $1)" >$1
    fi
}

append_if_not_exist() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        echo "$2" >>$1
    fi
}

pac_install() {
    sudo pacman -S --noconfirm --needed "$@"
}

yay_install() {
    sudo yay -S --noconfirm --needed "$@"
}

# Install utilities
pac_install unzip openssh network-manager-applet fzf xclip inetutils alacritty sxhkd wmctrl

# Install fonts
pac_install $(pacman -Ssq 'noto-fonts-*')

# Install AUR packages
# Install yay - AUR package manager
pacman -S --needed git base-devel && git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -si

yay_install visual-studio-code-bin google-chrome

# Awesome window manager
source "$(dirname "$0")/setup_awesomewm.sh"

# Configure HiDPI display
DPI_VALUE=144 # 96 * 1.5x
if ! grep -qF -- "Xft.dpi" ~/.Xresources; then
    echo "Xft.dpi: $DPI_VALUE" >>~/.Xresources
else
    sed -i "s/Xft.dpi:.*/Xft.dpi: $DPI_VALUE/" ~/.Xresources
fi
prepend_if_not_exist ~/.xinitrc "xrdb -merge ~/.Xresources"

# Auto-start MyScript
prepend_if_not_exist ~/.xinitrc "alacritty -e $HOME/MyScripts/myscripts --startup &"

# Setup audio
pac_install pulseaudio pavucontrol
pac_install alsa-utils # for amixer CLI command

# Bluetooth
pac_install bluez bluez-utils blueman
# then you can use bluetoothctl to pair in command line

# Setup input method
pac_install fcitx fcitx-configtool fcitx-googlepinyin
prepend_if_not_exist ~/.xinitrc "fcitx -d"
# sed -iE 's/#?TriggerKey=.*/TriggerKey=SHIFT_LSHIFT/' ~/.config/fcitx/config                                                             # set trigger key
# sed -iE 's/#?#UseExtraTriggerKeyOnlyWhenUseItToInactivate=.*/UseExtraTriggerKeyOnlyWhenUseItToInactivate=False/' ~/.config/fcitx/config # disable extra trigger key

# Configure Touchpad:
# https://wiki.archlinux.org/title/Touchpad_Synaptics
sudo tee /etc/X11/xorg.conf.d/70-synaptics.conf <<EOF
Section "InputClass"
    Identifier "touchpad"
    Option "tapping" "on"
    # Natural scrolling:
    Option "VertScrollDelta" "-111"
    Option "HorizScrollDelta" "-111"
EndSection
EOF

# Automatically run startx without using display manager / login manager.
append_if_not_exist \
    "$HOME/.bash_profile" \
    '[[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]] && startx'

# Automatically mount USB devices
pac_install udisks2 udiskie
prepend_if_not_exist ~/.xinitrc "udiskie &"

# Install dev tools
yay_install yarn mongodb-bin mongodb-tools-bin
sudo systemctl enable mongodb.service --now

# Install NVidia proprietary GPU driver.
if lspci -k | grep -A 2 -q -E "NVIDIA Corporation"; then
    pac_install nvidia-settings
fi

# Install GitHub CLI
if [[ -f "/etc/debian_version" ]]; then
    sudo apt-get update
    sudo apt install gh -y
elif [[ -f "/etc/arch-release" ]]; then
    pac_install github-cli
fi
[[ "$(gh auth status 2>&1)" =~ "not logged" ]] && gh auth login
