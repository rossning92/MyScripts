set -e
log_file="${MYSCRIPT_DATA_DIR}/MyScripts.log"
if [ -x "$(command -v klogg)" ]; then
  klogg --follow "$log_file"
elif [[ $(uname -s) == "Linux" ]]; then
  cat "$log_file" | run_script r/highlight.py -p "D:.*=blue" "W:.*=yellow" "E:.*=red" | less -iR +G
fi
