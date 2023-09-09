set -e
log_file="${MY_TEMP_DIR}/MyScripts.log"

#  less -R +G
tail -f -n +1 "$log_file" | run_script r/highlight.py -p "^.*? D .*=gray" "^.*? W .*=yellow" "^.*? E .*=red"
