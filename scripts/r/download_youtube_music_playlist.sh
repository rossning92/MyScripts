set -e
if [[ ! -x "$(command -v yt-dlp)" ]]; then
    pip install yt-dlp
fi
yt-dlp -x --audio-format mp3 --cookies youtube-cookies.txt -f bestaudio --ignore-errors "$1"
