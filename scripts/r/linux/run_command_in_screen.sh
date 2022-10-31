# mkdir ~/.screen || chmod 700 ~/.screen || true
# sudo /etc/init.d/screen-cleanup start

mkdir -p ~/.screen
chmod 700 ~/.screen # workaround for WSL
export SCREENDIR=$HOME/.screen

# Clean-up dead sessions
screen -wipe || true

out=$(screen -ls) || true
if [[ $out == *"screens on"* ]]; then
    echo "$out"
    read -p 'Please input session name: ' name
    screen -d -r $name # reattach
elif [[ $out == *"a screen on"* ]]; then
    screen -d -r # reattach
else
    screen -dmS et bash
    screen -r et -X stuff "$1\n"
    screen -r et
fi

# screen -r et -X quit || true
