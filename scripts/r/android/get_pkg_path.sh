adb shell "pm path {{PKG_NAME}} | sed -e 's/package://g' | sed -e 's/\/base\.apk//g'"
