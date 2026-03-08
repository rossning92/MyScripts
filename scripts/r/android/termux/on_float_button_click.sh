#!/bin/bash
tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT
fifo="$tmp_dir/stt_fifo"
tmp_file="$tmp_dir/stt.txt"
mkfifo "$fifo"

# Start STT in background, reading from FIFO for control signals
exec 3<>"$fifo"
bash "$HOME/MyScripts/bin/run_script" r/speech_to_text.py -o "$tmp_file" <&3 &
pid=$!

# Use termux-dialog sheet instead of confirm
res=$(termux-dialog sheet -t "Listening..." -v "Finish,Assistant,Cancel")
if echo "$res" | grep -q '"text": "Finish"'; then
    echo >&3 # Signal completion
    wait $pid
    if [[ -s "$tmp_file" ]]; then
        text=$(cat "$tmp_file")
        # Use clipboard for multiline, tabs, or non-ASCII (more reliable/faster)
        if [[ "$text" =~ [$'\n\t'] ]] || printf '%s' "$text" | LC_ALL=C grep -q '[^ -~]'; then
            termux-clipboard-set <"$tmp_file"
            su -c "input keyevent 279"
        else
            # Use 'input text' for simple ASCII strings
            su -c "input text $(printf '%q' "${text// /%s}")"
        fi
    fi
elif echo "$res" | grep -q '"text": "Assistant"'; then
    python "$HOME/MyScripts/bin/start_script.py" --run-in-tmux r/ai/assistant.sh --voice-input
    am start -n com.termux/com.termux.app.TermuxActivity
    printf '\e' >&3 # Signal abort
    wait $pid
else
    printf '\e' >&3 # Signal abort
    wait $pid
fi
exec 3>&-
