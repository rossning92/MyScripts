import re
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from _script import get_variable, set_variable
from utils.menu import Menu


@dataclass
class DeviceInfo:
    serial: str
    product_name: str
    battery_level: Optional[int]
    key: Optional[str]
    date_utc: Optional[float]
    is_current: bool


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

            # Get product name
            try:
                product_name = subprocess.check_output(
                    ["adb", "-s", serial, "shell", "getprop", "ro.product.name"],
                    universal_newlines=True,
                ).strip()

                date_utc = float(
                    subprocess.check_output(
                        ["adb", "-s", serial, "shell", "getprop", "ro.build.date.utc"],
                        universal_newlines=True,
                    ).strip()
                )

                # Get battery level
                out = subprocess.check_output(
                    ["adb", "-s", serial, "shell", "dumpsys", "battery"],
                    universal_newlines=True,
                )
                match = re.findall(r"level: (\d+)", out)
                if match:
                    battery_level = int(match[0])
                else:
                    battery_level = None
            except subprocess.CalledProcessError:
                continue

            # Find next unused key
            key = None
            for key in product_name:
                key = key.lower()
                if key not in used_key:
                    used_key.add(key)
                    break

            current_serial = get_variable("ANDROID_SERIAL")
            device_list.append(
                DeviceInfo(
                    serial=serial,
                    product_name=product_name,
                    battery_level=battery_level,
                    key=key,
                    date_utc=date_utc,
                    is_current=current_serial == serial,
                )
            )

    return device_list


def _update_device_list(
    devices: List[DeviceInfo],
    stop_event: threading.Event,
    update_event: threading.Event,
):
    while not stop_event.is_set():
        devices[:] = get_device_list()
        update_event.set()
        time.sleep(3)


class DeviceSelectMenu(Menu[DeviceInfo]):
    def __init__(self):
        self.__devices: List[DeviceInfo] = []

        # Create seperate thread to update device list
        self.__stop_event = threading.Event()
        self.__update_event = threading.Event()
        self.__device_update_thread = threading.Thread(
            target=lambda: _update_device_list(
                self.__devices, self.__stop_event, self.__update_event
            )
        )
        self.__device_update_thread.start()

        super().__init__(items=self.__devices)

    def on_exit(self):
        self.__stop_event.set()
        self.__device_update_thread.join()

    def on_char(self, ch: int | str) -> bool:
        if ch == "0":
            set_variable("ANDROID_SERIAL", "")
            return True
        elif type(ch) is str and ch >= "a" and ch <= "z":
            for device in self.__devices:
                if ch == device.key:
                    set_variable("ANDROID_SERIAL", device.serial)
                    device.is_current = True
                else:
                    device.is_current = False
            return True
        else:
            return super().on_char(ch)

    def get_item_text(self, item: DeviceInfo) -> str:
        bat = f"{item.battery_level:>3}%" if item.battery_level is not None else "n/a"
        s = f"[{item.key}] {item.product_name:<12} {item.serial:<15}  bat={bat}"
        if item.date_utc:
            s += f"  build_date={datetime.fromtimestamp(item.date_utc, timezone.utc)}"
        return s

    def get_item_color(self, item: DeviceInfo) -> str:
        if item.is_current:
            return "green"
        else:
            return super().get_item_color(item)

    def on_idle(self):
        if self.__update_event.isSet():
            self.__update_event.clear()
            self.update_screen()


if __name__ == "__main__":
    DeviceSelectMenu().exec()
