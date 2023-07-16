set -e
log_file="${MYSCRIPT_DATA_DIR}/MyScripts.log"
cat "$log_file" | run_script r/highlight.py -p "^D:.*=black" "^W:.*=yellow" "^E:.*=red" | less -iR +G
