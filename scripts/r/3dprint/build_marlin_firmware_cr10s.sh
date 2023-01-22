set -e

# https://docs.platformio.org/en/latest/core/installation/methods/pypi.html
pip install --user -U platformio

mkdir -p ~/Projects/MarlinFirmware
cd ~/Projects/MarlinFirmware

if [[ ! -d "Marlin" ]]; then
    git clone --single-branch --filter=blob:none -b 2.1.2 https://github.com/MarlinFirmware/Marlin
fi
if [[ ! -d "MarlinFirmware-Configurations" ]]; then
    git clone -b cr10s-skr-mini-e3-v3-bl-touch --single-branch --filter=blob:none https://github.com/rossning92/MarlinFirmware-Configurations
fi

if [[ -n "${_OPEN_VSCODE}" ]]; then
    run_script ext/open_in_editor.py .
fi

cp -r "MarlinFirmware-Configurations/config/examples/Creality/CR-10S/BigTreeTech SKR Mini E3 3.0/." Marlin/Marlin/

(
    cd Marlin
    sed -i 's/default_envs = mega2560/default_envs = STM32G0B1RE_btt/g' platformio.ini
    platformio run

    if [[ -n "${_FIRMWARE_OUT_DIR}" ]]; then
        cp ".pio/build/STM32G0B1RE_btt/firmware.bin" "${_FIRMWARE_OUT_DIR}/firmware.bin"
    elif [[ -n "${_FLASH_MARLIN_BFT}" ]]; then
        run_script r/3dprint/flash_firmware_marlin_bft.sh ".pio/build/STM32G0B1RE_btt/firmware.bin"
    else
        run_script ext/open.py .pio/build/STM32G0B1RE_btt
    fi
)
