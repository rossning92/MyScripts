set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"
    name="${file%.*}"
    name="${name//_/ }"

    # magick "$file" -pointsize 48 -background black -fill white label:"$name" -gravity Center -append "$out"
    magick "$file" -pointsize 36 -gravity North -fill red -annotate 0 "$name" "$out"
done
