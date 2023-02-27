set -e

out="$(adb shell getenforce | tr -d '\r')"
if [ "$out" != "Permissive" ]; then
    adb root
    adb shell "setenforce 0"
else
    echo 'SELinux is not enforced.'
fi
