set -e
if [[ -z "${GDRIVE_DIR}" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

source "$(dirname "$0")/_init_rclone.sh"

cd "$HOME"

sync_gdrive() {
    rclone bisync "drive:$1" "gdrive/$1" --progress --exclude=.mypy_cache "${@:2}"
}

for dir in $GDRIVE_DIR; do
    echo "Sync dir: $dir"

    # Create local directory if it does not exist
    mkdir -p "gdrive/${dir}"

    if ! sync_gdrive $dir; then
        printf "\n\n\n"
        read -p "Resync? (y/n): " ans
        if [[ "$ans" == "y" ]]; then
            sync_gdrive $dir --resync
        fi
    fi

    # Show all scripts in myscripts as gd/*
    abspath="$HOME/gdrive/$dir"
    if [ -x "$(command -v cygpath)" ]; then # For windows: convert from unix path to windows path
        abspath="$(cygpath -w "$abspath")"
    fi
done
