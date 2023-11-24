set -e

if [[ -z "${GDRIVE_DIR}" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

source "$(dirname "$0")/_init_rclone.sh"

cd "$HOME"

sync_gdrive() {
    rclone bisync "drive:$1" "$2" --verbose --progress --exclude=.mypy_cache "${@:3}"
}

[[ -z "$LOCAL_DIR" ]] && local_dir="$HOME/gdrive/$GDRIVE_DIR" || local_dir="$LOCAL_DIR"
[[ -x "$(command -v cygpath)" ]] && local_dir="$(cygpath -w "$local_dir")" # convert to win path
mkdir -p "$local_dir"                                                      # create local dir if not exists

echo "Bi-sync \"$GDRIVE_DIR\" <=> \"$local_dir\""
if ! sync_gdrive "$GDRIVE_DIR" "$local_dir"; then
    printf "\n\n\n"
    read -p "Resync? (y/n): " ans
    if [[ "$ans" == "y" ]]; then
        sync_gdrive "$GDRIVE_DIR" "$local_dir" --resync
    fi
fi
