#!/bin/bash

# CHANGE THESE FOR YOUR APP
app_package=""
dir_app_name=""

ADB="adb" # how you execute adb
ADB_SH="$ADB shell" # this script assumes using `adb root`. for `adb su` see `Caveats`

path_sysapp="/system/priv-app" # assuming the app is priviledged
apk_host="bin_vrdriver.apk"
apk_name=$dir_app_name".apk"
apk_target_dir="$path_sysapp/$dir_app_name"
apk_target_sys="$apk_target_dir/$apk_name"

# Install APK: using adb root
$ADB root 2> /dev/null
$ADB remount # mount system
$ADB push $apk_host $apk_target_sys

# Give permissions
$ADB_SH "chmod 755 $apk_target_dir"
$ADB_SH "chmod 644 $apk_target_sys"

#Unmount system
$ADB_SH "mount -o remount,ro /"

# Stop the app
$ADB shell "am force-stop $app_package"
