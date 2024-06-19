set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"
    name="${file%.*}"
    name="${name//_/ }"

    magick "$file" -geometry x{{IMAGE_HEIGHT}} "$out"
done
