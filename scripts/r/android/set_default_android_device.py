import re
import subprocess

from _script import set_variable
from _shutil import getch, print2


if __name__ == "__main__":
    lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split(
        "\n"
    )
    lines = lines[1:]
    serial_list = []
    for line in lines:
        if line.strip():
            serial, _ = line.split()
            serial_list.append(serial)

            # Get product name
            product = subprocess.check_output(
                ["adb", "-s", serial, "shell", "getprop", "ro.build.product"],
                universal_newlines=True,
            ).strip()

            # Get battery level
            out = subprocess.check_output(
                ["adb", "-s", serial, "shell", "dumpsys", "battery"],
                universal_newlines=True,
            )
            match = re.findall("level: (\d+)", out)
            if match:
                battery_level = match[0]
            else:
                battery_level = None

            print(
                "[%d] %s %s Battery=%s"
                % (len(serial_list), serial, product, battery_level)
            )

    serial_list.append("")
    print("[%d] clear ANDROID_SERIAL" % len(serial_list))

    ch = getch()
    index = ord(ch) - ord("1")
    if index >= 0 and index < len(serial_list):
        set_variable("ANDROID_SERIAL", serial_list[index])
        print2("Set default device to %s" % serial_list[index])
