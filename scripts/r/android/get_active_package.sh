adb shell "dumpsys activity activities" | awk '/mCurrentFocus|mFocusedApp|mFocusedWindow/ {split($NF, a, "/"); sub(/{/, "", a[1]); print a[1]; exit}'
