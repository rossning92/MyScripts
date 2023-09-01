if [[ ! -x "$(command -v google-chrome)" ]] && [[ ! -x "$(command -v google-chrome-stable)" ]]; then
    tmpdir=$(mktemp -d -p "$DIR")
    cd "$tmpdir"
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    sudo apt install ./google-chrome-stable_current_amd64.deb -y
    rm -rf "$WORK_DIR"
fi
