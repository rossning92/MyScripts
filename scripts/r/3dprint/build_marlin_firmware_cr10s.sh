set -e

# https://docs.platformio.org/en/latest/core/installation/methods/pypi.html
pip install --user -U platformio

mkdir -p ~/Projects/MarlinFirmware
cd ~/Projects/MarlinFirmware

git clone --single-branch --filter=blob:none https://github.com/MarlinFirmware/Marlin || true
git clone -b cr10s-skr-mini-e3-v3 --single-branch --filter=blob:none https://github.com/rossning92/MarlinFirmware-Configurations || true

run_script ext/open_in_editor.py .

cp -r "MarlinFirmware-Configurations/config/examples/Creality/CR-10S/BigTreeTech SKR Mini E3 3.0/." Marlin/Marlin/

(
    cd Marlin
    sed -i 's/default_envs = mega2560/default_envs = STM32G0B1RE_btt/g' platformio.ini
    platformio run
    run_script ext/open.py .pio/build/STM32G0B1RE_btt
)
