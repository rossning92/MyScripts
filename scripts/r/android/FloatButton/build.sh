#!/bin/bash
set -e
cd "$(dirname "$0")"
gradle assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk
adb shell appops set com.ross.floatbutton SYSTEM_ALERT_WINDOW allow
adb shell am start -n com.ross.floatbutton/.MainActivity
