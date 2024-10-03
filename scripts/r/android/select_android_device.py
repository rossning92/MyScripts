import subprocess
import sys
from typing import List, NamedTuple, Optional

from utils.getch import getch


class DeviceInfo(NamedTuple):
    serial: str
    flavor: str
    key: Optional[str]


def _print(s: str):
    print(s, end="", file=sys.stderr)


def get_device_list() -> List[DeviceInfo]:
    lines = subprocess.check_output(["adb", "devices"], universal_newlines=True).split(
        "\n"
    )
    lines = lines[1:]
    device_list = []
    used_key = set()
    for line in lines:
        if line.strip():
            serial, _ = line.split()

            # Get ro.build.flavor
            try:
                flavor = subprocess.check_output(
                    ["adb", "-s", serial, "shell", "getprop", "ro.build.flavor"],
                    universal_newlines=True,
                ).strip()
            except subprocess.CalledProcessError:
                continue

            # Find next unused key
            key = None
            for key in flavor:
                key = key.lower()
                if key not in used_key:
                    used_key.add(key)
                    break

            _print(f"[{key}] {serial}")
            _print(" %s" % flavor)
            device_list.append(
                DeviceInfo(
                    serial=serial,
                    flavor=flavor,
                    key=key,
                )
            )
            _print("\n")

    _print("[0] Clear ANDROID_SERIAL")
    _print("\n")
    return device_list


def select_android_device() -> Optional[str]:
    device_list = get_device_list()
    ch = getch()
    for device in device_list:
        if ch == device.key:
            return device.serial
    return None


if __name__ == "__main__":
    s = select_android_device()
    print(s, end="")
