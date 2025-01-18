set -e
{{ include('r/linux/_select_service.sh') }}
sudo systemctl stop $service
sudo systemctl status $service
