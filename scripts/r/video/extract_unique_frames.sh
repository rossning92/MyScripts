set -e
input="$1"
out_dir="${input%.*}_frames"
mkdir -p "$out_dir"
ffmpeg -i "$input" -qscale:v 2 -filter_complex "select=bitor(gt(scene\,0.0001)\,eq(n\,0))" -vsync drop "$out_dir/%04d.jpg"
