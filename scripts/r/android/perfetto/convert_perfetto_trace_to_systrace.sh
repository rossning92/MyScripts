set -e
input_filename=$(basename "$1")
input_filename_without_extension="${input_filename%.*}"
input_directory=$(dirname "$1")

tmpdir=$(dirname $(mktemp -u))
cd "$tmpdir"
curl -LO https://get.perfetto.dev/traceconv
chmod +x traceconv

./traceconv systrace "$1" "${input_directory}/${input_filename_without_extension}.txt"
