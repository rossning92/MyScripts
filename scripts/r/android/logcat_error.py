from _android import *

# adb shell "logcat | grep --color=always -E ' F libc |Abort message: '"

logcat(level="E|F", ignore_duplicates=True)
