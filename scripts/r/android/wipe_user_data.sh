set -e
read -p "Dangerous! Press enter to continue..."

adb reboot bootloader
fastboot wait-for-device
fastboot erase misc
fastboot erase userdata
fastboot erase metadata
fastboot reboot
