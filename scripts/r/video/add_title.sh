set -e

folder=$(dirname "$1")
cd "$folder"
mkdir -p out

file=$(basename "$1")
if [ -n "${2:-}" ]; then
	text="$2"
else
	text="${file}"
	text="${text%.*}"
	text="${text//_/ }"
fi

fontfile=$HOME/.local/share/fonts/SourceHanSansSC-Bold.otf
fontsize=72

ffmpeg -hide_banner -loglevel error -stats -i "$1" -filter_complex "[0:v]drawtext=text='${text}':bordercolor=black:borderw=4:fix_bounds=true:fontfile=${fontfile}:fontsize=${fontsize}:fontcolor=white:x=(w-text_w)/2:y=48" "out/$file" -y
