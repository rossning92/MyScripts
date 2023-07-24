if ! [ -x "$(command -v rclone)" ]; then
    if command -v termux-setup-storage; then # is running in termux
        pkg install rclone -y
    else
        sudo -v
        curl https://rclone.org/install.sh | sudo bash
    fi
fi

if [[ $(rclone config file) =~ "doesn't exist" ]]; then
    rclone config create drive drive
fi
