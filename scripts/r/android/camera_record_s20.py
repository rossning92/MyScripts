from _android import *
from _script import *

if is_locked():
    run_script("/r/android/unlock.sh")


@menu_item(key="r")
def start_recording():
    adb_shell("settings put system screen_off_timeout 60000")

    # Kill the camera app.
    adb_shell("am force-stop com.sec.android.app.camera")

    # Launch camera app
    adb_shell("am start -n com.sec.android.app.camera/.Camera")
    sleep(3)

    adb_shell("input keyevent KEYCODE_DPAD_UP")
    adb_shell("input keyevent KEYCODE_DPAD_UP")
    adb_shell("input keyevent KEYCODE_DPAD_RIGHT")
    sleep(3)

    # Press volume key to start recording.
    adb_shell("input keyevent KEYCODE_VOLUME_DOWN")

    # echo 'Manual focus at center.'
    adb_shell("input tap 540 1296")

    print2("Press `s` to stop recording...", color="green")


@menu_item(key=" ")
def stop_recording():
    # Press volume key to stop recording.
    adb_shell("input keyevent KEYCODE_VOLUME_DOWN")
    sleep(2)


@menu_item(key="p")
def pull_last_file():
    file = adb_shell("ls /sdcard/DCIM/Camera | tail -n 1", check_output=True).strip()
    if not os.path.exists(file):
        subprocess.check_call(["adb", "pull", "/sdcard/DCIM/Camera/%s" % file])
    call_echo(["mpv", file])


if __name__ == "__main__":
    menu_loop()

