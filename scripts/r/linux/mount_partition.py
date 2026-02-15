import json
import os
import subprocess
from dataclasses import dataclass
from typing import List, Literal

from utils.menu import Menu

CRYPT_BASENAME = "crypt"


@dataclass
class _Part:
    name: str
    type: Literal["part", "dm", "crypt"]
    mountpoint: str
    fstype: str
    size: str
    label: str


def _get_available_mapper_name() -> str:
    counter = 1
    while os.path.exists(f"/dev/mapper/{CRYPT_BASENAME}{counter}"):
        counter += 1
    return f"{CRYPT_BASENAME}{counter}"


def _get_partitions() -> List[_Part]:
    partitions: List[_Part] = []

    result = subprocess.run(
        ["lsblk", "-o", "name,type,size,label,mountpoint,fstype", "-J"],
        capture_output=True,
        text=True,
        check=True,
    )
    data = json.loads(result.stdout)

    dev_queue = []
    for device in data.get("blockdevices", []):
        if "children" in device:
            dev_queue.extend(device["children"])
    while dev_queue:
        dev = dev_queue.pop(0)
        partitions.append(
            _Part(
                name=dev["name"],
                type=dev["type"],
                mountpoint=dev.get("mountpoint", ""),
                fstype=dev.get("fstype", ""),
                size=dev.get("size", ""),
                label=dev.get("label", ""),
            )
        )
        if "children" in dev:
            dev_queue.extend(dev["children"])

    return partitions


class DiskMountMenu(Menu[_Part]):
    def __init__(self):
        super().__init__(prompt="partitions", items=_get_partitions())

    def on_enter_pressed(self):
        part = self.get_selected_item()
        if not part:
            return

        if part.fstype == "crypto_LUKS":
            self.run_raw(
                lambda: subprocess.check_call(
                    [
                        "sudo",
                        "cryptsetup",
                        "open",
                        f"/dev/{part.name}",
                        _get_available_mapper_name(),
                    ]
                )
            )
            self.close()
        elif part.type == "crypt":
            self.run_raw(
                lambda: subprocess.check_call(
                    [
                        "sudo",
                        "cryptsetup",
                        "close",
                        part.name,
                    ]
                )
            )
            self.close()


if __name__ == "__main__":
    DiskMountMenu().exec()
