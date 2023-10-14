set -e

append_if_not_exist() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        echo "$2" >>$1
    fi
}

append_if_not_exist "$HOME/.bashrc" 'export SCREENDIR=$HOME/.screen; [ -d $SCREENDIR ] || mkdir -p -m 700 $SCREENDIR'

source "$(dirname "$0")/enable_systemd.sh"

source "$(dirname "$0")/setup_wsl_vpnkit.sh"

# Shutdown WSL to take effect.
wsl.exe --shutdown
