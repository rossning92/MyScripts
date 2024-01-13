set -e

name=test
sudo tee /opt/${name}_service.sh <<EOF
ping 127.0.0.1
EOF

sudo tee /etc/systemd/system/${name}.service <<-EOF
[Unit]
Description=${name} systemd service unit file.

[Service]
ExecStart=/bin/bash /opt/${name}_service.sh

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl restart ${name}.service --now

sudo journalctl -u ${name}.service -f
