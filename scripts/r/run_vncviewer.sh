pwd=$(run_script r/linux/encrypt_vncpasswd.sh ${VNC_PASSWORD})

cd ~
cat >connection.vnc <<EOF
ConnMethod=tcp
FullScreen=1
Host=${VNC_SERVER}
Password=${pwd}
EOF

"C:\Program Files\RealVNC\VNC Viewer\vncviewer.exe" -config connection.vnc &
