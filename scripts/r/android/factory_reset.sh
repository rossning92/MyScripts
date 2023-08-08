read -p "Dangerous!!! Confirm?"

echo 'Reboot to bootloader...'
adb reboot bootloader || true
# fastboot wait-for-device

echo 'Erase userdata...'
fastboot erase userdata
fastboot erase cache

echo 'Reboot...'
fastboot reboot
