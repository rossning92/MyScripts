set -e
if [[ -z "${GDRIVE_DIR}" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

if [[ $(rclone config file) =~ "doesn't exist" ]]; then
    rclone config create drive drive
fi

cd ~

# Create local directory if it does not exist
mkdir -p "gdrive/${GDRIVE_DIR}"

sync_gdrive() {
    rclone bisync "drive:${GDRIVE_DIR}" "gdrive/${GDRIVE_DIR}" --progress --verbose "$@"
}

if ! sync_gdrive; then
    read -p "resync? (y/n)" ans
    if [[ "$ans" == 'y' ]]; then
        sync_gdrive --resync
        sync_gdrive
    fi
fi
