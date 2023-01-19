set -e
cd "$(dirname "$1")"

input="$1"
output="${input%.*}.md"

pandoc --extract-media . -t gfm-raw_html "$input" -o "$output"
