#!/bin/bash

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
tmp_file="$tmp_dir/stt.txt"
fifo="$tmp_dir/stt_fifo"
mkfifo "$fifo"

# exec 3<> "$fifo" keeps it open so it doesn't close after one write
exec 3<>"$fifo"
bash "$HOME/MyScripts/bin/run_script" r/speech_to_text.py -o "$tmp_file" <&3 &
pid=$!

confirm_res=$(termux-dialog confirm -i "Listening...")
confirm_choice=$(echo "$confirm_res" | sed -n 's/.*"text": "\(.*\)".*/\1/p')

if [[ "$confirm_choice" == "yes" ]]; then
    echo "" >&3
    wait $pid
    if [[ -f "$tmp_file" ]]; then
        text=$(cat "$tmp_file")
        if [[ -n "$text" ]]; then
            # Use clipboard paste for multiline/tabbed or non-ASCII content.
            if [[ "$text" == *$'\n'* || "$text" == *$'\t'* ]] || printf '%s' "$text" | LC_ALL=C grep -q '[^ -~]'; then
                termux-clipboard-set <"$tmp_file"
                su -c "input keyevent 279"
            else
                safe_text=${text// /%s}
                safe_text=$(printf '%q' "$safe_text")
                su -c "input text $safe_text"
            fi
        fi
    fi
else
    printf '\e' >&3
    wait $pid
fi
exec 3>&-
