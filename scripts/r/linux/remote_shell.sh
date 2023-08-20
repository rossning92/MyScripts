set -e

source "$(dirname "$0")/screen/_wsl_screen_workaround.sh"

# Clean-up dead sessions
screen -wipe 2>&1 >/dev/null || true

if [[ -n "${SCREEN_SESSION_NAME}" ]]; then
    screen -d -r "${SCREEN_SESSION_NAME}"
else
    out=$(screen -ls) || true
    if [[ $out == *"screens on"* ]]; then
        echo "$out"
        read -p 'Please input session name: ' name
        screen -d -r $name # reattach
    elif [[ $out == *"a screen on"* ]]; then
        screen -d -r # reattach
    else
        echo 'no active session.'
        exit 1
    fi
fi
