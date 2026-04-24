#!/bin/bash
toast() {
    termux-toast -s -b green -c black "$1" &
}

DIR="$TMPDIR/termux_stt"
mkdir -p "$DIR"
LOCK="$DIR/listening.pid"
FIFO="$DIR/listening.fifo"

# Toggle: If already listening, signal completion and exit
if PID=$(cat "$LOCK" 2>/dev/null) && kill -0 "$PID" 2>/dev/null; then
    toast "PROCESSING..."
    echo >"$FIFO"
    exit 0
fi

# Initialization
echo $$ >"$LOCK"
[[ -p "$FIFO" ]] || mkfifo "$FIFO"
OUT=$(mktemp)
trap 'rm -f "$LOCK" "$FIFO" "$OUT"' EXIT

toast "LISTENING..."

# Start STT (blocks until FIFO receives input)
exec 3<>"$FIFO"
bash "$HOME/myscripts/bin/run_script" r/speech_to_text.py -o "$OUT" <&3

# Handle result
if [[ -s "$OUT" ]]; then
    TEXT=$(<"$OUT")
    # Use clipboard for multiline or non-ASCII; 'input text' for simple strings
    if [[ "$TEXT" =~ [$'\n\t'] ]] || printf '%s' "$TEXT" | LC_ALL=C grep -q '[^ -~]'; then
        termux-clipboard-set <"$OUT"
        su -c "input keyevent 279"
    else
        su -c "input text $(printf '%q' "${TEXT// /%s}")"
    fi
fi
