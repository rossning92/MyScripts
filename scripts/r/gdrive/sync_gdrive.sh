set -e

# env: GDRIVE_DIR
# env: LOCAL_DIR

if [[ -z "$GDRIVE_DIR" ]]; then
    echo 'ERROR: GDRIVE_DIR cannot be empty.'
    exit 1
fi

source "$(dirname "$0")/_init_rclone.sh"

cd "$HOME"

rclone_wrapper() {
    logfile="$(mktemp)"

    # --progress : enable progress bar
    rclone bisync "drive:$1" "$2" --verbose --exclude=.mypy_cache/** "${@:3}" 2>&1 | tee "$logfile"
    ret=${PIPESTATUS[0]}
    if [[ "$ret" != "0" ]]; then
        echo "ERROR: rclone returned $ret"
        if grep -q 'too many deletes' "$logfile"; then
            read -p "Too many deletes, force sync? (y/n): " ans
            if [[ "$ans" == "y" ]]; then
                rclone_wrapper "$@" --force
            fi
        elif grep -q 'cannot find prior' "$logfile"; then
            read -p "First time sync? (y/n): " ans
            if [[ "$ans" == "y" ]]; then
                rclone_wrapper "$@" --resync
            fi
        fi
    fi
}

[[ -z "$LOCAL_DIR" ]] && local_dir="$HOME/gdrive/$GDRIVE_DIR" || local_dir="$LOCAL_DIR"
[[ -x "$(command -v cygpath)" ]] && local_dir="$(cygpath -w "$local_dir")" # convert to win path
mkdir -p "$local_dir"                                                      # create local dir if not exists

echo "Sync \"gdrive://$GDRIVE_DIR\" <=> \"$local_dir\""
rclone_wrapper "$GDRIVE_DIR" "$local_dir"
