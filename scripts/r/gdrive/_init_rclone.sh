if [[ $(rclone config file) =~ "doesn't exist" ]]; then
    rclone config create drive drive
fi
