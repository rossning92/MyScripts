set -e

if [[ -f "/etc/debian_version" ]]; then
    sudo apt-get update

    # Install Github CLI
    sudo apt install gh -y
elif [[ -f "/etc/arch-release" ]]; then
    sudo pacman -S --noconfirm github-cli
fi

[[ "$(gh auth status 2>&1)" =~ "not logged" ]] && gh auth login

# Install Chrome
run_script r/linux/install_google_chrome.sh

# Update DPI scale
DPI_VALUE=144 # 96 * 1.5x
if ! grep -qF -- "Xft.dpi" ~/.Xresources; then
    echo "Xft.dpi: $DPI_VALUE" >>~/.Xresources
else
    sed -i "s/Xft.dpi:.*/Xft.dpi: $DPI_VALUE/" ~/.Xresources
fi
