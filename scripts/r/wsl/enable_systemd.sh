# https://devblogs.microsoft.com/commandline/systemd-support-is-now-available-in-wsl/
set -e

sudo tee /etc/wsl.conf <<-EOF
[boot]
systemd=true
EOF

wsl.exe --shutdown
