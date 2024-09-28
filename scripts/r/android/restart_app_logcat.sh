export PKG_NAME='{{PKG_NAME}}'
run_script r/android/restart_app.py
run_script r/android/logcat_for_pkg.sh
