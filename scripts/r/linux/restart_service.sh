set -e
{{ include('r/linux/_select_service.sh') }}
sudo systemctl daemon-reload
sudo systemctl enable $service
sudo systemctl restart $service --now
systemctl status $service
journalctl -u $service --follow
