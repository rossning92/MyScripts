import ctypes
import subprocess

from _android import wait_until_boot_complete


def get_screen_size():
    user32 = ctypes.windll.user32
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


win_pos = [int(x) for x in "{{_POS}}".split()]

while True:
    wait_until_boot_complete()

    args = [
        "scrcpy",
        "--always-on-top",
    ]

    if win_pos:
        args += [
            "--window-x",
            "%s" % win_pos[0],
            "--window-y",
            "%s" % win_pos[1],
        ]

    if "{{_SIZE}}":
        args += ["--max-size", "{{_SIZE}}"]

    ps = subprocess.Popen(args, stdin=subprocess.PIPE)
    if ps.stdin:
        ps.stdin.close()

    try:
        ps.wait()
    except KeyboardInterrupt:
        print("Exiting...")
