import logging
import re
import subprocess
import threading
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


def _get_device_info(serial: str) -> DeviceInfo:
    product_name = "n/a"
    date_utc: Optional[float] = None
    battery_level = None

    try:
        product_name = subprocess.check_output(
            ["adb", "-s", serial, "shell", "getprop", "ro.product.name"],
            universal_newlines=True,
            stderr=subprocess.DEVNULL,
        ).strip()

        date_utc = float(
            subprocess.check_output(
                ["adb", "-s", serial, "shell", "getprop", "ro.build.date.utc"],
                universal_newlines=True,
                stderr=subprocess.DEVNULL,
            ).strip()
        )

        batt_out = subprocess.check_output(
            ["adb", "-s", serial, "shell", "dumpsys", "battery"],
            universal_newlines=True,
            stderr=subprocess.DEVNULL,
        )
        match = re.findall(r"level: (\d+)", batt_out)
        battery_level = int(match[0]) if match else None
    except subprocess.CalledProcessError:
        pass

    return DeviceInfo(
        serial=serial,
        product_name=product_name,
        battery_level=battery_level,
        key="",
        date_utc=date_utc,
        is_current=False,
    )


def _update_device_list(
    devices: List[DeviceInfo],
    stop_event: threading.Event,
):
    proc: Optional[subprocess.Popen[str]] = None
    try:
        proc = subprocess.Popen(
            ["adb", "track-devices"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        while not stop_event.is_set():
            if proc.stdout is None:
                break

            header = proc.stdout.read(4)
            if not header:
                if proc.poll() is not None:
                    break
                continue

            length = int(header, 16)
            payload = proc.stdout.read(length)
            for line in payload.split("\n"):
                if not line:
                    continue

                serial, state = line.split("\t", 1)
                devices[:] = [device for device in devices if device.serial != serial]
                if state != "device":
                    continue

                devices.append(_get_device_info(serial))

            # Update current device
            current_serial = get_variable("ANDROID_SERIAL")
            for device in devices:
                device.is_current = device.serial == current_serial

            # Update key
            used_keys = {device.key for device in devices if device.key}
            for device in devices:
                key = None
                for ch in device.product_name.lower():
                    if "a" <= ch <= "z" and ch not in used_keys:
                        key = ch
                        used_keys.add(ch)
                        break
                device.key = key
    except Exception:
        logging.exception("Failed to track adb devices")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()


class DeviceSelectMenu(Menu[DeviceInfo]):
    def __init__(self):
        self.__devices: List[DeviceInfo] = []

        # Create seperate thread to update device list
        self.__stop_event = threading.Event()
        self.__device_update_thread = threading.Thread(
            target=lambda: _update_device_list(self.__devices, self.__stop_event),
            daemon=True,
        )
        self.__device_update_thread.start()

        super().__init__(items=self.__devices, prompt="devices")

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
        self.update_screen()


if __name__ == "__main__":
    DeviceSelectMenu().exec()
