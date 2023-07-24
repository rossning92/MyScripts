set -e
if [[ -z "${GDRIVE_DIR}" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

source "$(dirname "$0")/_init_rclone.sh"

cd "$HOME"

# Create local directory if it does not exist
mkdir -p "gdrive/${GDRIVE_DIR}"

sync_gdrive() {
    rclone bisync "drive:${GDRIVE_DIR}" "gdrive/${GDRIVE_DIR}" --verbose "$@"
}

if ! sync_gdrive; then
    printf "\n\n\n"
    read -p "Resync (Y/n): " ans
    if [[ "$ans" == "y" ]] || [[ -z "$ans" ]]; then
        sync_gdrive --resync
        sync_gdrive
    fi
fi

# Show all scripts in myscripts as gd/*
abspath="$HOME/gdrive/${GDRIVE_DIR}"
if [ -x "$(command -v cygpath)" ]; then # For windows: convert from unix path to windows path
    abspath="$(cygpath -w "$abspath")"
fi

run_script ext/add_script_dir.py gd "$abspath"
