set -e

cd ~/Desktop/
device="$(run_script r/android/get_device_name.sh | tr -d '\r')"
date="$(date +%Y%m%d_%H%M%S)"
fname="logcat_${device}_${date}.log"

adb logcat -c

bash "$(dirname "$0")/logcat_non_stop.sh" >$fname 2>$fname &

run_script r/logviewer.py "$fname"
