import os
import subprocess


def get_screen_resolution():
    if os.name == "nt":
        import ctypes

        user32 = ctypes.windll.user32
        return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    else:
        return 1920, 1080


def _main():
    args = ["scrcpy", "--window-title=scrcpy"]

    sw, sh = get_screen_resolution()
    args += [
        "--always-on-top",
        "--window-x",
        "0",
        "--window-y",
        str(sh - 200),
    ]

    serial = os.environ.get("ANDROID_SERIAL")
    if serial:
        args += ["--serial", serial]

    if os.environ.get("SCRCPY_HEIGHT"):
        args += ["--max-size", os.environ["SCRCPY_HEIGHT"]]

    ps = subprocess.Popen(args, stdin=subprocess.PIPE)
    ps.stdin.close()  # to avoid stuck in "press any key..."
    ps.wait()


if __name__ == "__main__":
    _main()
