pwd=$(run_script r/linux/encrypt_vncpasswd.sh ${VNC_PASSWORD})

if [[ -n "${VNC_FULLSCEREN}" ]]; then
    fullscreen=1
else
    fullscreen=0
fi

if [[ -z "$VNC_QUALITY" ]]; then
    quality="Medium"
fi

cd ~
rm connection.vnc || true
cat >connection.vnc <<EOF
ConnMethod=tcp
FullScreen=${fullscreen}
Quality=${quality}
Host=${VNC_SERVER}
Password=${pwd}
EOF

if [[ "$(uname)" == "linux"* || "$(uname)" == "Linux"* ]]; then
    if ! command -v vncviewer &>/dev/null; then
        if [[ -f "/etc/arch-release" ]]; then
            echo 'Installing VNC Viewer...'
            yay -S --noconfirm realvnc-vnc-viewer
        else
            echo 'Download and install VNC Viewer...'
            url="https://downloads.realvnc.com/download/file/viewer.files/VNC-Viewer-7.5.1-Linux-x64.deb"
            deb_file="VNC-Viewer.deb"
            wget "$url" -O "$deb_file"
            sudo dpkg -i "$deb_file"
            rm "$deb_file"
            echo 'VNC Viewer installed successfully.'
        fi
    fi

    killall vncviewer
    nohup vncviewer -config ~/connection.vnc &
elif [[ "$(uname -o)" == "Msys" ]]; then
    taskkill /f /im vncviewer.exe
    "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" -config connection.vnc &
else
    echo "Unsupported OS: $(uname)"
fi
