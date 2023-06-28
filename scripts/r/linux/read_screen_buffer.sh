set -e

# Workaround for WSL: `Cannot make directory '/run/screen': Permission denied`
if [[ $(grep -i microsoft /proc/version) ]]; then
    mkdir -p ~/.screen
    chmod 700 ~/.screen
    export SCREENDIR=$HOME/.screen
fi

screen -S od -X hardcopy /tmp/screen_buffer.txt
cat /tmp/screen_buffer.txt
