set -e
cp "$1" "$1.bak"
pdftk "$1.bak" cat end-1 output "$1"
