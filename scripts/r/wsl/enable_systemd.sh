set -e

# https://devblogs.microsoft.com/commandline/systemd-support-is-now-available-in-wsl/
sudo tee /etc/wsl.conf <<-EOF
[boot]
systemd=true
EOF
