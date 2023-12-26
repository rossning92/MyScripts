# https://wiki.archlinux.org/title/x11vnc

set -e

if [[ ! -x "$(command -v x11vnc)" ]]; then
    if [[ -f "/etc/arch-release" ]]; then
        sudo pacman -S --noconfirm x11vnc
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
killall x11vnc || true
nohup x11vnc -many -usepw -display :0 2>/dev/null >/dev/null &
