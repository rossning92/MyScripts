set -e
cd "$(dirname "$1")"
mkdir -p "out"

magick "$@" "out/combined.pdf"
