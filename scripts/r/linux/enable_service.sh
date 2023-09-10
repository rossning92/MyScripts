set -e
selected=$(systemctl list-unit-files --all | fzf)
service=$(echo "$selected" | awk '{print $1}')
systemctl enable $service --now
systemctl status $service
