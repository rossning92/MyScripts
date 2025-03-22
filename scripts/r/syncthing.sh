set -e

syncthing generate

syncthing -no-browser 2>&1 | {
    tee /dev/tty |
        while IFS= read -r line; do
            if echo "$line" | grep -q 'listening on'; then
                syncthing cli config defaults device auto-accept-folders set true
            fi
        done
}
