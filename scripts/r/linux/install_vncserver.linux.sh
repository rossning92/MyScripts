# https://wiki.archlinux.org/title/TigerVNC#With_xprofile

set -e

if [[ ! -x "$(command -v x0vncserver)" ]]; then
    if [[ -f "/etc/arch-release" ]]; then
        sudo pacman -S --noconfirm tigervnc
    else
        sudo apt update
        sudo apt-get install tigervnc-scraping-server -y
    fi
fi

# Setup VNC password
if [[ ! -f ~/.vnc/passwd ]]; then
    vncpasswd
fi

# Start x0vncserver automatically
file_prepend() {
    if [[ ! -f $1 ]] || ! grep -qF -- "$2" $1; then
        printf '%s\n%s\n' "$2" "$(cat $1)" >$1
    fi
}
file_prepend ~/.xinitrc "x0vncserver -rfbauth ~/.vnc/passwd &"

# Run x0vncserver now
killall x0vncserver || true
nohup x0vncserver -rfbauth ~/.vnc/passwd 2>/dev/null >/dev/null &
