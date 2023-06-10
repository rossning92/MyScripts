#!/bin/bash
set -e
cd "$(dirname "$0")"

source clone_marlin_firmware_cr10s.sh

(
    cd Marlin
    sed -i 's/default_envs = mega2560/default_envs = STM32G0B1RE_btt/g' platformio.ini
    platformio run

    if [[ -n "${FLASH_MARLIN_BFT}" ]]; then
        run_script r/3dprint/flash_firmware_marlin_bft.sh ".pio/build/STM32G0B1RE_btt/firmware.bin"
    else
        run_script ext/open.py ".pio/build/STM32G0B1RE_btt"
    fi
)
