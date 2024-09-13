set -e
cd "$(dirname "$1")"

mkdir -p "out"

IFS=',' read -r x y w h <<<"$CROP_RECT"

for file in "$@"; do
    file="$(basename "$file")"
    out="out/$file"

    magick "$file" -crop "${w}x${h}+${x}+${y}" "$out"
done
