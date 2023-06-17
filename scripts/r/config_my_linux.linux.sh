set -e

sudo apt-get update

# Install Github CLI
sudo apt install gh -y
[[ "$(gh auth status 2>&1)" =~ "not logged" ]] && gh login auth

# Install Chrome
run_script r/linux/install_google_chrome.sh

# Update DPI scale
DPI_VALUE=144 # 96 * 1.5x
touch $HOME/.Xresources
sed -i "s/Xft.dpi:.*/Xft.dpi: $DPI_VALUE/" "$HOME/.Xresources"
