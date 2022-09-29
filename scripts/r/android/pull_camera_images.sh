set -e
cd ~/Desktop

adb pull /sdcard/DCIM/Camera

read -p "press <enter> to remove camera images..."

adb shell rm -rf /sdcard/DCIM/Camera
