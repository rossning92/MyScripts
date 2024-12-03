export PKG_NAME='{{PKG_NAME}}'

adb logcat -c

{{ include('r/android/kill_app.sh', {'PKG_NAME': PKG_NAME}) }}

run_script r/android/logcat_for_pkg.sh &
sleep 3

run_script r/android/restart_app.py
