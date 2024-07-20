set -e

unset MSYS_NO_PATHCONV

cd "$(dirname "$1")"
mkdir -p "out"

magick "$@" {{if PAGE_SIZE_LETTER}}-page letter{{end}} "out/combined.pdf"
