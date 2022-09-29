from _shutil import call_echo
from _script import run_script

if __name__ == "__main__":
    run_script("unlock.sh")

    call_echo('adb shell "am start -a android.media.action.VIDEO_CAPTURE"')
    call_echo('adb shell "input keyevent KEYCODE_VOLUME_DOWN"')

    input("Press enter to stop...")
    call_echo('adb shell "input keyevent KEYCODE_VOLUME_DOWN"')
    call_echo('adb shell "input keyevent KEYCODE_ENTER"')
