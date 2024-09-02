set -e
# Config thermald
# https://github.com/linux-surface/linux-surface/tree/master/contrib/thermald
echo 'Setup thermald...'
sudo pacman -S thermald --noconfirm
sudo cp "$(dirname "$0")/../../../../settings/linux-surface/thermal-conf.xml" /etc/thermald/thermal-conf.xml
sudo systemctl enable thermald.service --now
