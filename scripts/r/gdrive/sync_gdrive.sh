set -e
if [[ $(rclone config file) =~ "doesn't exist" ]]; then
    rclone config create drive drive
fi

cd ~
mkdir -p "gdrive/${GDRIVE_SYNC_DIR}"
rclone sync "drive:${GDRIVE_SYNC_DIR}" "gdrive/${GDRIVE_SYNC_DIR}" --progress

run_script ext/open.py "gdrive/${GDRIVE_SYNC_DIR}"
