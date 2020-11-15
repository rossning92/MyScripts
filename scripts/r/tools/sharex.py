from _shutil import *


def kill_proc():
    while subprocess.call('tasklist | find "ShareX.exe"', shell=True) == 0:
        subprocess.call("taskkill /im ShareX.exe")
        time.sleep(0.5)


def install_sharex():
    exe_path = r"C:\Program Files\ShareX\ShareX.exe"
    if not exists(exe_path):
        run_elevated("choco install sharex -y")

    setting_path = expandvars(r"%USERPROFILE%\Documents\ShareX")
    if not exists(setting_path):
        subprocess.Popen([exe_path, "-silent"], close_fds=True)

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

    subprocess.Popen([exe_path, "-silent"], close_fds=True)


if __name__ == "__main__":
    if sys.platform == "win32":
        install_sharex()
