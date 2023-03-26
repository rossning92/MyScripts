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
    print "\n\n\n"
    read -p "resync? (Y/n)" ans
    if [[ -z "$ans" ]]; then
        sync_gdrive --resync
        sync_gdrive
    fi
fi

if [[ -n "${_PREFIX}" ]]; then
    abspath="$HOME/gdrive/${GDRIVE_DIR}"
    # Windows: convert UNIX to windows path
    if ! [ -x "$(command -v labtest)" ]; then
        abspath="$(cygpath -w "$abspath")"
    fi

    run_script ext/add_script_dir.py "${_PREFIX}" "$abspath"
fi
