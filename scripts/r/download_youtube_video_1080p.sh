set -e

if [[ -n "$VIDEO_DOWNLOAD_DIR" ]]; then
    mkdir -p "$VIDEO_DOWNLOAD_DIR"
    cd "$VIDEO_DOWNLOAD_DIR"
fi

# https://github.com/yt-dlp/yt-dlp#format-selection
yt-dlp -S "res:1080" --no-mtime "$1" --no-playlist

run_script r/save_video_url.py "$1"
