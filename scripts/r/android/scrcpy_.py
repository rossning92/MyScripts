from _shutil import call_echo
from _android import wait_until_boot_complete
import subprocess

while True:
    wait_until_boot_complete()

    args = [
        "scrcpy",
        "--always-on-top",
        "--window-x",
        "20",
        "--window-y",
        "20",
    ]
    if "{{_SIZE}}":
        args += ["--max-size", "{{_SIZE}}"]

    ps = subprocess.Popen(args, stdin=subprocess.PIPE)
    ps.stdin.close()
    ps.wait()