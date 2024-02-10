set -e
selected=$(systemctl list-unit-files --all | fzf)
service=$(echo "$selected" | awk '{print $1}')

sudo systemctl daemon-reload
sudo systemctl enable $service
sudo systemctl restart $service --now
systemctl status $service
journalctl -u $service
