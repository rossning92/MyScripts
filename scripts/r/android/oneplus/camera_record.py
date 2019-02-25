from _shutil import *
from _script import *

run_script('unlock.sh')

call('adb shell "am start -a android.media.action.VIDEO_CAPTURE"')

call('adb shell "input keyevent KEYCODE_VOLUME_DOWN"')

input('Press enter to stop...')
call('adb shell "input keyevent KEYCODE_VOLUME_DOWN"')

call('adb shell "input keyevent KEYCODE_ENTER"')
