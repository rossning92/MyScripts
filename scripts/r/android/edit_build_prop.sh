set -e

adb root
adb remount

cd "$(mktemp -d)"
adb pull /system/build.prop

vim build.prop

adb push build.prop /system/build.prop
