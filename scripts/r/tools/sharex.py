import json
import os
import subprocess
import sys
import time


def kill_proc():
    while subprocess.call('tasklist | find "ShareX.exe"', shell=True) == 0:
        subprocess.call("taskkill /im ShareX.exe")
        time.sleep(0.5)


def run_sharex():
    sharex = r"C:\Program Files\ShareX\ShareX.exe"

    setting_path = os.path.expandvars(r"%USERPROFILE%\Documents\ShareX")
    if not os.path.exists(setting_path):
        subprocess.Popen([sharex, "-silent"], close_fds=True)

    kill_proc()

    config_file = os.path.join(setting_path, "ApplicationConfig.json")
    with open(config_file) as f:
        config = json.load(f)

    config["DefaultTaskSettings"]["UploadSettings"][
        "NameFormatPattern"
    ] = "%yy%mo%d%h%mi%s_%ms"
    config["DefaultTaskSettings"]["UploadSettings"][
        "NameFormatPatternActiveWindow"
    ] = "%yy%mo%d%h%mi%s_%ms"
    # config["DefaultTaskSettings"]["CaptureSettings"]["FFmpegOptions"]
    config["DefaultTaskSettings"]["CaptureSettings"]["ShowCursor"] = False
    config["AutoCheckUpdate"] = False

    with open(config_file, "w") as f:
        json.dump(config, f)

    # config_file = os.path.join(setting_path, "HotkeysConfig.json")
    # config = json.load(open(config_file))
    # config["Hotkeys"][0]["HotkeyInfo"]["Hotkey"] = "F1"
    # json.dump(config, open(config_file, "w"))

    subprocess.Popen([sharex, "-silent"], close_fds=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        run_sharex()
