set -e

wait_for_key() {
    echo "(press 'q' to stop recoding...)"
    while [[ "$ans" != "q" ]]; do
        read -n1 ans
    done
}

if [[ -z "$1" ]]; then
    echo "ERROR: must provide a file." >&2
    exit 1
fi

if command -v termux-setup-storage; then # is running in termux
    termux-microphone-record -f "$1"

    wait_for_key

    termux-microphone-record -q

elif [[ "$OSTYPE" == "linux-gnu"* ]]; then # is linux
    run_script r/require_package.py sox

    rec "$1" &
    pid=$!

    wait_for_key

    kill -INT $pid
else
    echo 'ERROR: not implemented.'
    exit 1
fi
