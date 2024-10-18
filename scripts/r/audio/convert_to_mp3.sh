set -e

unset MSYS_NO_PATHCONV

cd "$(dirname "$1")"

ffmpeg -i "$1" -codec:a libmp3lame -qscale:a 5 "${1%.*}.mp3"
