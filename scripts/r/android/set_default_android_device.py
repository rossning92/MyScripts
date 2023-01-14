import re
import subprocess
from collections import namedtuple

from _script import get_variable, set_variable
from _shutil import getch, print2

DeviceInfo = namedtuple("DeviceInfo", ["serial", "product", "battery_level"])


def get_device_list():
    current_serial = get_variable("ANDROID_SERIAL")
    print("ANDROID_SERIAL = %s" % current_serial)
    print()

    lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split(
        "\n"
    )
    lines = lines[1:]
    device_list = []
    for line in lines:
        if line.strip():
            serial, _ = line.split()

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
                "[%s] %s"
                % (
                    product[0].lower(),
                    serial,
                ),
                end="",
            )
            print2(" %s" % product, color="green", end="")
            print(" Battery=%s" % battery_level, end="")
            if current_serial == serial:
                print2(" (current)", color="red", end="")
            device_list.append(DeviceInfo(serial, product, battery_level))
            print()

    print("[0] clear ANDROID_SERIAL")
    print()
    return device_list


def select_default_android_device():
    while True:
        device_list = get_device_list()
        ch = getch()
        for device in device_list:
            if ch == device.product[0].lower():
                set_variable("ANDROID_SERIAL", device.serial)
                print2("Set default device to %s" % device.serial)
                return
            elif ch == "0":
                set_variable("ANDROID_SERIAL", "")
                print2("Cleared ANDROID_SERIAL")
                return


if __name__ == "__main__":
    select_default_android_device()
