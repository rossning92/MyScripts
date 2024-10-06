set -e
{{ include('r/linux/_select_service.sh') }}
journalctl -u $service -f
