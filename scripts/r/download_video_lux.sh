set -e

cd "$VIDEO_DOWNLOAD_DIR"

export PATH="$(echo $HOME/go/bin):$PATH"

cookie_file="$HOME/.bilibili-cookies.txt"
cookie="$(cat "$cookie_file")"
url="$1"
shift
extra_args="$@"

for attempt in $(seq 1 3); do
    echo "Download attempt $attempt for $url"
    if lux -c "$cookie" $extra_args "$url"; then
        break
    fi
    if [ "$attempt" -eq 3 ]; then
        echo "Download failed after 3 attempts" >&2
        exit 1
    fi
done

run_script r/save_video_url.py "$url"
