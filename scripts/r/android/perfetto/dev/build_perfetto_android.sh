# https://perfetto.dev/docs/contributing/build-instructions#standalone-builds

set -e

source "$(dirname "$0")/_setup_perfetto_project.sh"

tools/install-build-deps --android

tools/gn args out/android

tools/ninja -C out/android

adb root
adb remount
adb push out/android/traced /system/bin/
adb push out/android/libperfetto.so /system/lib64/
adb push out/android/libperfetto_android_internal.so /system/lib64/
