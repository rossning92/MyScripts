set -e

adb reboot bootloader
fastboot format userdata
fastboot reboot
