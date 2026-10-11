set -e

cd "$VIDEO_DOWNLOAD_DIR"

export PATH="$(echo $HOME/go/bin):$PATH"

cookie_args=()
if [ -n "${BILIBILI_COOKIE_FILE:-}" ]; then
    cookie_args=(-c "$(cat "$BILIBILI_COOKIE_FILE")")
fi
url="$1"
shift
extra_args="$@"

for attempt in $(seq 1 3); do
    echo "Download attempt $attempt for $url"
    if lux "${cookie_args[@]}" $extra_args "$url"; then
        break
    fi
    if [ "$attempt" -eq 3 ]; then
        echo "Download failed after 3 attempts" >&2
        exit 1
    fi
done

run_script r/save_video_url.py "$url"
