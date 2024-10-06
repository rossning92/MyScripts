set -e
{{ include('r/linux/_select_service.sh') }}
sudo systemctl disable $service --now
sudo systemctl status $service
