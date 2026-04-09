# Workaround for WSL1: `Cannot make directory '/run/screen': Permission denied`
if ! grep -q "WSL2" /proc/version; then
    mkdir -p ~/.screen
    chmod 700 ~/.screen
    export SCREENDIR=$HOME/.screen
fi
