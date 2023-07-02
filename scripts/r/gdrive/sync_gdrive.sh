set -e
if [[ -z "${GDRIVE_DIR}" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

if ! [ -x "$(command -v rclone)" ]; then
    sudo -v
    curl https://rclone.org/install.sh | sudo bash
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
    printf "\n\n\n"
    read -p "Resync (y/n): " ans
    if [[ "$ans" == "y" ]]; then
        sync_gdrive --resync
        sync_gdrive
    fi
fi

# Show all scripts in myscripts as gd/*
abspath="$HOME/gdrive/${GDRIVE_DIR}"
# Windows: convert UNIX to windows path
if command -v cygpath; then
    abspath="$(cygpath -w "$abspath")"
fi

run_script ext/add_script_dir.py gd "$abspath"
