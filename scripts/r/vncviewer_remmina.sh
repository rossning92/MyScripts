set -e

if [[ -z "$VNC_SERVER" ]]; then
    echo 'ERROR: Must specify VNC_SERVER'
    exit 1
fi

mkdir -p "$HOME/.local/share/remmina"
profile_path="$HOME/.local/share/remmina/$VNC_SERVER.remmina"
if [[ ! -f "$profile_path" ]]; then
    cat >"$profile_path" <<EOF
[remmina]
name=$VNC_SERVER
server=$VNC_SERVER
protocol=VNC
viewmode=1
scale=1
keyboard_grab=1
EOF
fi

nohup remmina "$profile_path" 2>/dev/null >/dev/null &
