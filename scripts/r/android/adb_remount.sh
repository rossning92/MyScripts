# https://android.googlesource.com/platform/system/core/+/master/fs_mgr/README.overlayfs.md

adb root

{{# adb remount -R won’t reboot if the device is already in the adb remount state.}}
adb remount -R

{{ include('r/android/wait_boot_completed.sh') }}

adb root
adb remount
