set -e
input="$1"
out_dir="${input%.*}_frames"
mkdir -p "$out_dir"
ffmpeg -i "$input" -qscale:v 2 "$out_dir/%04d.jpg"
