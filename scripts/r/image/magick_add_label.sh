set -e
cd "$(dirname "$1")"
mkdir -p "out"
file="$(basename "$1")"
out="out/$file"
name="${file%.*}"

magick "$1" -pointsize 36 -background black -fill white label:"$name" -gravity Center -append "$out"
