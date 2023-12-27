set -e
selected=$(systemctl list-unit-files --all | fzf)
service=$(echo "$selected" | awk '{print $1}')
systemctl restart $service --now
systemctl status $service
