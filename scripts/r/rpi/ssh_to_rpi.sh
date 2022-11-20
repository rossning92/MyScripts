set -e
echo 'Scan IP address for Raspberry Pi...'
rpi_ip=$(run_script scan_network.py --vendor "Pi" --show_ipv4)

echo "Connect to ${rpi_ip}..."
SSH_HOST=${rpi_ip} SSH_USER=pi SSH_PWD=raspberry run_script r/linux/ssh.sh
