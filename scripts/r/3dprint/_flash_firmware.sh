set -e
cd ~
if [[ ! -d "marlin-binary-protocol" ]]; then
    git clone --single-branch --filter=blob:none https://github.com/trippwill/marlin-binary-protocol
fi
python3 marlin-binary-protocol/transfer.py firmware.bin firmware.bin --reset
