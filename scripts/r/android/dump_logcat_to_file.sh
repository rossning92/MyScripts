set -e
cd $HOME/Desktop
echo 'Clear logcat buffer...'
adb logcat -c

if [[ -n "$1" ]]; then
    fname="$1"
else
    fname="logcat_$(date +%Y%m%d_%H%M%S).log"
fi
echo "Dump to $fname"
stdbuf -o0 adb logcat >$fname &
run_script ext/open.py $fname
wait
