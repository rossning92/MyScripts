set -e
cd ~/Desktop

adb bugreport

latest_bugreport=$(find . -name "bugreport-*" -type f -printf "%T@ %p\n" | sort -n | tail -1 | cut -d' ' -f2-)
run_script r/unzip.py $latest_bugreport
