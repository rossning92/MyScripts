set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"
    name="${file%.*}"
    name="${name//_/ }"

    magick "$file" -pointsize 48 -gravity North -fill red -annotate 0 "$name" "$out"
done
