from _android import logcat
from _shutil import call2

call2("adb wait-for-device")
logcat(
    regex=r"{{_REGEX}}" if r"{{_REGEX}}" else r"ROSS:| F libc |Abort message:",
)
