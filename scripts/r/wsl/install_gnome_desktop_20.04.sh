# https://gist.github.com/SlvrEagle23/ce9e28adcec55504f3ed7d1fdc8ef573
set -e

sudo apt-get update -y
sudo apt-get upgrade -y

# Installing common deps
sudo apt install ubuntu-desktop gnome -y

# cat >>~/.bashrc <<EOF
# export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
# export LIBGL_ALWAYS_INDIRECT=1
# EOF

# Enable systemd
mkdir -p ~/Downloads
cd ~/Downloads
git clone https://github.com/DamionGans/ubuntu-wsl2-systemd-script.git
cd ubuntu-wsl2-systemd-script/
bash ubuntu-wsl2-systemd-script.sh

wsl.exe --shutdown
