pwd=$(run_script r/linux/encrypt_vncpasswd.sh ${VNC_PASSWORD})

if [[ -n "${VNC_FULLSCEREN}" ]]; then
    fullscreen=1
else
    fullscreen=0
fi

cd ~
rm connection.vnc || true
cat >connection.vnc <<EOF
ConnMethod=tcp
FullScreen=${fullscreen}
Host=${VNC_SERVER}
Password=${pwd}
EOF

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    vncviewer -config ~/connection.vnc &
elif [[ "$OSTYPE" == "msys" ]]; then
    "C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" -config connection.vnc &
else
    echo "Unsupported OS: ${OSTYPE}."
fi
