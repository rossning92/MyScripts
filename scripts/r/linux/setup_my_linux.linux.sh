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

# Install utilities
sudo pacman -S --noconfirm unzip openssh network-manager-applet fzf xclip

# Install GitHub CLI
if [[ -f "/etc/debian_version" ]]; then
    sudo apt-get update
    sudo apt install gh -y
elif [[ -f "/etc/arch-release" ]]; then
    sudo pacman -S --noconfirm github-cli
fi
[[ "$(gh auth status 2>&1)" =~ "not logged" ]] && gh auth login

# Install Chrome
run_script r/linux/install_google_chrome.sh

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
sudo pacman -S --noconfirm pulseaudio
sudo pacman -S --noconfirm alsa-utils # for amixer CLI command

# Setup input method
sudo pacman -S --noconfirm fcitx fcitx-configtool fcitx-googlepinyin
prepend_if_not_exist ~/.xinitrc "fcitx -d"
sed -iE 's/#?TriggerKey=.*/TriggerKey=SHIFT_LSHIFT/' ~/.config/fcitx/config                                                             # set trigger key
sed -iE 's/#?#UseExtraTriggerKeyOnlyWhenUseItToInactivate=.*/UseExtraTriggerKeyOnlyWhenUseItToInactivate=False/' ~/.config/fcitx/config # disable extra trigger key

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
