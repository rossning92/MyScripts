opacity=80
blur_radius=10
dx=10
dy=10

input_file="$1"
base="$(basename "$input_file")"
name="${base%.*}"
output_file="${name}_shadow.png"

magick "$input_file" \( +clone -background black -shadow "${opacity}x${blur_radius}+${dx}+${dy}" \) +swap -background none -layers merge +repage "$output_file"
