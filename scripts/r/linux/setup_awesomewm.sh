set -e

if [ ! -x "$(command -v awesome)" ]; then
    sudo apt install awesome -y
fi

# Copy awesome config file
mkdir -p "$HOME/.config/awesome/"
ln -sf "$(dirname "$0")/../../../settings/awesome/rc.lua" $HOME/.config/awesome/rc.lua
