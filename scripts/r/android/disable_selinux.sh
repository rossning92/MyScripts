set -e

out="$(adb shell getenforce | tr -d '\r')"
if [ "$out" != "Permissive" ]; then
    adb root
    adb shell "setenforce 0"

    # No need: the above takes effect immediately
    # adb shell "stop;start"
    # run_script wait_hmd_to_boot
    # run_script disable_prox
else
    echo 'SELinux is not enforced.'
fi
