set -e

file="$1"
if [[ -z "$file" ]]; then
    echo "Error: file parameter is required."
    exit 1
fi

filter_path="$MY_DATA_DIR/log_filters"
while true; do
    options="(all)\n$(find "$filter_path" -type f -name "*.txt" -exec basename {} .txt \;)"
    choice=$(echo -e "$options" | fzf)

    if [[ "$choice" == '(all)' ]]; then
        cat "$file"
    else
        patt="$(cat "$filter_path/$choice.txt")"
        grep -E "$patt" "$file"
    fi | grep -E "^[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3}" | sort | run_script r/highlight.py -p "^.*? D .*=gray" "^.*? W .*=yellow" "^.*? (E|F) .*=red" | less -iNSR
done
