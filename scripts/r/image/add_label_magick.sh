set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"
    name="${file%.*}"
    name="${name//_/ }"

    magick "$file" -pointsize {{ADD_LABEL_FONT_SIZE_PT}} -gravity North -fill {{ADD_LABEL_COLOR}} -annotate 0 "$name" "$out"
done
