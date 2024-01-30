set -e

device="$(run_script r/android/get_device_name.sh | tr -d '\r')"
date="$(date +%Y%m%d_%H%M%S)"
logfile="logcat_${device}_${date}.log"

echo "Stream logcat to \"$logfile\""
adb logcat -c
stdbuf -o0 adb logcat >"$logfile" &
pid=$!

while ! grep -q "$1" "$logfile"; do
    sleep 1
done

echo "Found logcat line \"$1\", exiting."
kill $pid
rm "$logfile"
