set -e

unset MSYS_NO_PATHCONV

cd "$(dirname "$1")"
mkdir -p "out"

magick "$@" "out/combined.pdf"
