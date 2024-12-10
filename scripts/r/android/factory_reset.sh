read -p "Dangerous!!! Confirm?"

echo 'Reboot to bootloader...'
adb reboot bootloader || true
# fastboot wait-for-device

fastboot oem factory-reset
fastboot erase misc
fastboot reboot

# echo 'Erase userdata...'
# fastboot format userdata
# fastboot erase misc
# fastboot erase userdata
# fastboot erase metadata
