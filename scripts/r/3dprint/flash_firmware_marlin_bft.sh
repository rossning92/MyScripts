set -e

if [[ ! -f "$1" ]]; then
    echo "invalid firmware bin path: '$1'"
fi
run_script r/linux/push_file_ssh.py "$1"

run_script ext/run_script_ssh.py --host ${PRINTER_3D_HOST} \
    --user ${PRINTER_3D_USER} \
    --pwd ${PRINTER_3D_PWD} \
    "$(dirname "$0")/_flash_firmware.sh"
