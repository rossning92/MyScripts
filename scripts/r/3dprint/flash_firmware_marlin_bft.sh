set -e

if [[ ! -f "$1" ]]; then
    echo "Invalid firmware bin path: '$1'"
fi
run_script r/linux/push_file_ssh.py "$1"

flash_script="$(dirname "$0")/_flash_firmware_bft.sh"
if [[ "$(uname -o)" == "Msys" ]]; then
    flash_script=$(cygpath -w "$flash_script")
fi

run_script ext/run_script_ssh.py --host ${PRINTER_3D_HOST} \
    --user ${PRINTER_3D_USER} \
    --pwd ${PRINTER_3D_PWD} \
    "$flash_script"
