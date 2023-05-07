set -e
run_script ext/install_pkg.py screen

# HACK: for WSL
if [[ $(grep Microsoft /proc/version) ]]; then
    mkdir -p ~/.screen
    chmod 700 ~/.screen
    export SCREENDIR=$HOME/.screen
fi

# Clean-up dead sessions
screen -wipe 2>&1 >/dev/null || true

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
