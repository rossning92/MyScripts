set -e
in_file="$1"
out_file="${in_file%.*}.p{{_RANGE}}.pdf"
pdftk "$1" cat {{_RANGE}} output "$out_file"
