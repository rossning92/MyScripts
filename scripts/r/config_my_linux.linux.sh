# sudo apt update
# sudo apt install xserver-xorg-input-synaptics -y

# Disable all animations
kwriteconfig5 --file ~/.config/kwinrc --group Compositing --key Enabled false

# Don't group taskbar icons
kwriteconfig5 --file ~/.config/plasma-org.kde.plasma.desktop-appletsrc --group Containments --group 2 --group Applets --group 28 --group Configuration --group General --key groupingStrategy 0

# Start an empty session when logged in
kwriteconfig5 --file ~/.config/ksmserverrc --group General --key loginMode emptySession

kquitapp5 plasmashell
kstart5 plasmashell
