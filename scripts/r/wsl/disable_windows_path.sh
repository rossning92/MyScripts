sudo bash -c 'cat >/etc/wsl.conf <<EOF
[interop]
appendWindowsPath = false
EOF'

wsl --shutdown