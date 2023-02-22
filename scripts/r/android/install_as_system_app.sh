#!/bin/bash
set -e

pkg="${_PKG}"
app_dir_name="${_APP_DIR_NAME}"

adb root
adb remount

priv_app_path="/system/priv-app" # assuming the app is priviledged
src_apk="${_APK}"
apk_name=${app_dir_name}".apk"
apk_target_dir="${priv_app_path}/${app_dir_name}"
apk_target_sys="${apk_target_dir}/${apk_name}"

# Install APK
adb shell mkdir -p "${apk_target_dir}"
adb push "${src_apk}" "${apk_target_sys}"

# Set permissions
adb shell "chmod 755 ${apk_target_dir}"
adb shell "chmod 644 ${apk_target_sys}"

# Unmount system
# adb shell "mount -o remount,ro /"

# Stop the app
adb shell "am force-stop $pkg"
