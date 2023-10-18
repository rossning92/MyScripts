set -e
cd $HOME/Desktop
echo 'Clear logcat buffer...'
adb logcat -c

if [[ -n "$1" ]]; then
    fname="$1"
else
    device="$(run_script r/android/get_device_name.sh | tr -d '\r')"
    date="$(date +%Y%m%d_%H%M%S)"
    fname="logcat_${device}_${date}.log"
fi

echo "Dump logcat to $fname"
stdbuf -o0 adb logcat >$fname &
run_script ext/open.py $fname
wait
