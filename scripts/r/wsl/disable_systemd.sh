set -e
if [ ! -f /etc/wsl.conf ]; then
    echo 'disabled systemd.'
    sudo sed -i '/systemd=true/d' /etc/wsl.conf

    wsl.exe --shutdown
fi
