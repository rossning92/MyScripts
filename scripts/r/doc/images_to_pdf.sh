set -e

unset MSYS_NO_PATHCONV

cd "$(dirname "$1")"

magick "$@" {{if PAGE_SIZE_LETTER}}-page letter{{end}} "${1%.*}.pdf"
