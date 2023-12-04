echo '>>> SUMMARY <<<'
adb shell "dumpsys activity activities | grep -E '(Display|Stack) #|\* Task|Hist'"

echo '>>> dumpsys activity activities <<<'
adb shell "dumpsys activity activities"
