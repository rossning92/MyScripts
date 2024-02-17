set -e

prepend_line_dedup() {
    # Remove the line if it exists and then prepend it
    if [[ -f "$1" ]] && grep -qF -- "$2" "$1"; then
        repl=$(printf '%s\n' "$2" | sed -e 's/[]\/$*.^[]/\\&/g')
        sed -i "\%^$repl$%d" "$1"
    fi
    printf '%s\n%s\n' "$2" "$(cat $1)" >"$1"
}

append_line_dedup() {
    # Remove the line if it exists and then append it
    if [[ -f "$1" ]] && grep -qF -- "$2" "$1"; then
        repl=$(printf '%s\n' "$2" | sed -e 's/[]\/$*.^[]/\\&/g')
        sed -i "\%^$repl$%d" "$1"
    fi
    echo "$2" >>"$1"
}

append_line_sudo() {
    if [[ ! -f $1 ]] || ! sudo grep -qF -- "$2" $1; then
        echo "$2" | sudo tee -a $1
    fi
}

pac_install() {
    sudo pacman -S --noconfirm --needed "$@"
}

yay_install() {
    yay -S --noconfirm --needed "$@"
}

# Install utilities
pac_install git unzip openssh fzf xclip inetutils alacritty sxhkd wmctrl less vim

# Install fonts
pac_install $(pacman -Ssq 'noto-fonts-*')

# Install yay - AUR package manager: https://github.com/Jguer/yay#binary
if [[ ! -x "$(command -v yay)" ]]; then
    sudo pacman -S --needed git base-devel && git clone https://aur.archlinux.org/yay-bin.git && cd yay-bin && makepkg -si
fi

yay_install visual-studio-code-bin google-chrome

# Configure HiDPI display
DPI_VALUE=144 # 96 * 1.5x
if ! grep -qF -- "Xft.dpi" ~/.Xresources; then
    echo "Xft.dpi: $DPI_VALUE" >>~/.Xresources
else
    sed -i "s/Xft.dpi:.*/Xft.dpi: $DPI_VALUE/" ~/.Xresources
fi
# This should be the first line of .xinitrc, so that all other apps can get the correct DPI value.
prepend_line_dedup ~/.xinitrc "xrdb -merge ~/.Xresources"

# Network manager
pac_install network-manager-applet
append_line_dedup ~/.xinitrc "nm-applet &"

# Bluetooth
# - bluez and bluez-utils: a Linux Bluetooth stack
# - blueman: GUI tool for desktop environments
pac_install bluez bluez-utils blueman
append_line_dedup ~/.xinitrc "blueman-applet &"
sudo systemctl enable bluetooth.service --now
# then you can use bluetoothctl to pair in command line

# Setup audio
pac_install pulseaudio pavucontrol pulseaudio-bluetooth
pac_install alsa-utils # for amixer CLI command

# Setup input method
# pac_install fcitx fcitx-configtool fcitx-googlepinyin
# append_line_dedup ~/.xinitrc "fcitx -d"
# # Set trigger key: left shift
# sed -iE 's/#?TriggerKey=.*/TriggerKey=SHIFT_LSHIFT/' ~/.config/fcitx/config
# # Disable extra trigger key
# sed -iE 's/#?#UseExtraTriggerKeyOnlyWhenUseItToInactivate=.*/UseExtraTriggerKeyOnlyWhenUseItToInactivate=False/' ~/.config/fcitx/config

# https://wiki.archlinux.org/title/Fcitx5
pac_install fcitx5 fcitx5-qt fcitx5-gtk fcitx5-config-qt fcitx5-chinese-addons
append_line_dedup ~/.xinitrc "fcitx5 -d"

# Key mapping using https://github.com/rvaiya/keyd
# Map CapsLock to Control+Meta key
yay_install keyd
sudo tee /etc/keyd/default.conf <<EOF
[ids]
*
[main]
capslock = overload(capslock, esc)

[capslock:C-M]
EOF
sudo systemctl enable keyd.service --now

# Automatically run startx without using display manager / login manager.
append_line_dedup \
    "$HOME/.bash_profile" \
    '[[ -z $DISPLAY ]] && [[ $(tty) = /dev/tty1 ]] && startx'

# Automatically mount USB devices
pac_install udisks2 udiskie
append_line_dedup ~/.xinitrc "udiskie &"

# Install window manager
source "$(dirname "$0")/setup_awesomewm.sh"

# Install dev tools
yay_install yarn mongodb-bin mongodb-tools-bin
sudo systemctl enable mongodb.service --now

# Install NVidia proprietary GPU driver.
if lspci -k | grep -A 2 -q -E "NVIDIA Corporation"; then
    pac_install nvidia-settings
fi

# Hardware specific (TODO: move)
yay_install k380-function-keys-conf
pac_install solaar # Logitech device manager
append_line_dedup ~/.xinitrc 'solaar --window hide &'

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

# Screenshot
pac_install flameshot
append_line_dedup ~/.xinitrc 'flameshot &'

# Auto-start MyScript
append_line_dedup ~/.xinitrc 'alacritty -e "$HOME/MyScripts/myscripts" --startup &'

# Replace the current process with the awesomewm when initializing X.
append_line_dedup ~/.xinitrc "exec awesome"

# Disable sudo password
append_line_sudo /etc/sudoers "$(whoami) ALL=(ALL:ALL) NOPASSWD: ALL"

# Install GitHub CLI
pac_install github-cli
if [[ "$(gh auth status 2>&1)" =~ "not logged" ]]; then
    gh auth login
fi
