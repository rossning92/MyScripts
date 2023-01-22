set -e

killall -9 pronsole || true

cd ~
if [[ ! -d "marlin-binary-protocol" ]]; then
    git clone --single-branch --filter=blob:none https://github.com/trippwill/marlin-binary-protocol
fi
port=$(ls /dev/ttyACM* | sed -n 1p)
python3 marlin-binary-protocol/transfer.py firmware.bin firmware.bin --reset -p ${port}
