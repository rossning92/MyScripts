set -e

if [[ ! -f "$1" ]]; then
    echo "invalid firmware bin path: '$1'"
fi
run_script r/linux/push_file_ssh.py "$1"

cd /tmp
(
    cat >flash_firmware.sh <<EOF
set -e
cd ~
if [[ ! -d "marlin-binary-protocol" ]]; then
    git clone --single-branch --filter=blob:none https://github.com/trippwill/marlin-binary-protocol
fi
python3 marlin-binary-protocol/transfer.py firmware.bin firmware.bin --reset
EOF
    run_script ext/run_script_ssh.py flash_firmware.sh
)
