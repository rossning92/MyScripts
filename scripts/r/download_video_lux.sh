set -e

cd "$VIDEO_DOWNLOAD_DIR"

export PATH=$(echo $HOME/go/bin):$PATH

cookie_file="$HOME/.bilibili-cookies.txt"
cookie="$(cat "$cookie_file")"
url="$1"

lux -c "$cookie" "$url"

run_script r/save_video_url.py "$url"
