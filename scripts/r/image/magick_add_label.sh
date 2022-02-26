set -e
cd "$(dirname "$1")"

mkdir -p "out"
file="$(basename "$1")"
out="out/$file"
name="${file%.*}"

# magick "$file" -pointsize 48 -background black -fill white label:"$name" -gravity Center -append "$out"
magick "$file" -pointsize 100 -gravity Center -stroke black -fill white -annotate 0 "$name" "$out"
