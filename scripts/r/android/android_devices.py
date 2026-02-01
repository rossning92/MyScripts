import logging
import subprocess
import threading
from dataclasses import dataclass
from typing import List, Optional

from _script import get_variable, set_variable
from utils.menu import Menu


@dataclass
class DeviceInfo:
    serial: str
    product_name: str
    battery_level: Optional[int]
    key: Optional[str]
    is_current: bool


def _update_device_list(
    devices: List[DeviceInfo],
    stop_event: threading.Event,
):
    proc: Optional[subprocess.Popen[str]] = None
    try:
        proc = subprocess.Popen(
            ["adb", "track-devices", "-l"],
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

            new_devices = []
            current_serial = get_variable("ANDROID_SERIAL")
            for line in payload.splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    info = dict(part.split(":", 1) for part in parts[2:] if ":" in part)
                    new_devices.append(
                        DeviceInfo(
                            serial=parts[0],
                            product_name=info.get("product", "n/a"),
                            battery_level=None,
                            key=None,
                            is_current=parts[0] == current_serial,
                        )
                    )

            # Update key
            used_keys = set()
            for device in new_devices:
                for ch in device.product_name.lower():
                    if "a" <= ch <= "z" and ch not in used_keys:
                        device.key = ch
                        used_keys.add(ch)
                        break

            devices[:] = new_devices

    except Exception:
        logging.exception("Failed to track adb devices")
    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()


def _update_battery_levels(
    devices: List[DeviceInfo],
    stop_event: threading.Event,
):
    while not stop_event.is_set():
        for device in list(devices):
            if stop_event.is_set():
                break
            try:
                res = subprocess.run(
                    ["adb", "-s", device.serial, "shell", "dumpsys battery"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if "level:" in line:
                            device.battery_level = int(line.split(":")[1].strip())
                            break
            except Exception:
                pass
        stop_event.wait(10)


class DeviceSelectMenu(Menu[DeviceInfo]):
    def __init__(self):
        self.__devices: List[DeviceInfo] = []

        self.__stop_event = threading.Event()

        self.__device_update_thread = threading.Thread(
            target=lambda: _update_device_list(self.__devices, self.__stop_event),
            daemon=True,
        )
        self.__device_update_thread.start()

        self.__battery_update_thread = threading.Thread(
            target=lambda: _update_battery_levels(self.__devices, self.__stop_event),
            daemon=True,
        )
        self.__battery_update_thread.start()

        super().__init__(items=self.__devices, prompt="devices")

    def on_exit(self):
        self.__stop_event.set()
        self.__device_update_thread.join()
        self.__battery_update_thread.join()

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
