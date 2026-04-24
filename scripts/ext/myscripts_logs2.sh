set -e
log_file="${MY_TEMP_DIR}/myscripts.log"

#  less -R +G
tail -f -n +1 "$log_file" | grep --line-buffered -v ' D ' | run_script r/highlight.py -p "^.*? D .*=gray" "^.*? W .*=yellow" "^.*? E .*=red"
