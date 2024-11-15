# https://wiki.archlinux.org/title/NoMachine

set -e

yay -S nomachine --noconfirm

# By default, the nxd service is set to manual start instead of automatic. Therefore, upon starting the nxserver systemd service, you can't connect because nxd has not started. Now set it to automatic start:
run sudo /usr/NX/bin/nxserver --startmode nxd automatic

sudo systemctl restart nxserver --now
