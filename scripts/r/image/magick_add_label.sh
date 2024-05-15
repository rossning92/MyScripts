set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"
    name="${file%.*}"
    name="${name//_/ }"

    magick "$file" -pointsize {{_FONT_SIZE_PT}} -gravity North -fill white -annotate 0 "$name" "$out"
done
