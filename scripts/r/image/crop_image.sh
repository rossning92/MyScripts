set -e
cd "$(dirname "$1")"

mkdir -p "out"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"

    magick "$file" -crop "{{CROP_W}}x{{CROP_H}}+{{CROP_X}}+{{CROP_Y}}" "$out"
done
