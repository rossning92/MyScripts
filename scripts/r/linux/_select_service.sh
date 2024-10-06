selected=$(systemctl list-unit-files --all | fzf)
service=$(echo "$selected" | awk '{print $1}')
