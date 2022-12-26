@echo off
cmd /c sdkmanager "extras;google;auto"
cd C:\Android\android-sdk\extras\google\auto


adb shell am start com.google.android.projection.gearhead/.companion.settings.DefaultSettingsActivity
echo Click "three dots" and choose "Start head unit server".
pause

adb forward tcp:5277 tcp:5277
desktop-head-unit
