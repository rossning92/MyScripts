set -e
{{ include('r/linux/_select_service.sh') }}
sudo systemctl start $service
sudo systemctl status $service
