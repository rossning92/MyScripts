set -e

if [ $# -eq 0 ]; then
	echo "Usage: $0 <svg-file> [<svg-file> ...]" >&2
	exit 1
fi

for file in "$@"; do
	dirname="$(dirname "$file")"
	filename="$(basename "$file")"
	name="${filename%.*}"

	magick -density 400 -background None "$file" -resize "x256" "$dirname/$name.png"
done
