set -e

sudo apt-get update

# Install Github CLI
sudo apt install gh -y
[[ "$(gh auth status 2>&1)" =~ "not logged" ]] && gh login auth

# Install Chrome
run_script r/linux/install_google_chrome.sh

# Install KDE
sudo apt install kde-plasma-desktop -y
sudo apt install plasma-nm -y

# sudo apt install xserver-xorg-input-synaptics -y

# Disable all animations
kwriteconfig5 --file ~/.config/kwinrc --group Compositing --key Enabled false

# Don't group taskbar icons
kwriteconfig5 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc --group Containments --group 2 --group Applets --group 28 --group Configuration --group General --key groupingStrategy 0

# Start an empty session when logged in
kwriteconfig5 --file ~/.config/ksmserverrc --group General --key loginMode emptySession

kquitapp5 plasmashell
kstart5 plasmashell
