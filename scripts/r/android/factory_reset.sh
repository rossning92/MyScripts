read -p "Dangerous!!! Confirm?"

echo 'Reboot to bootloader...'
adb reboot bootloader || true
# fastboot wait-for-device

echo 'Erase userdata...'
fastboot --set-active=b
fastboot format userdata
# fastboot erase misc
# fastboot erase userdata
# fastboot erase metadata

echo 'Reboot...'
fastboot reboot
