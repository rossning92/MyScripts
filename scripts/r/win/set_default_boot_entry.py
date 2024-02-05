#!/usr/bin/env python

import subprocess

from utils.menu import Menu

if __name__ == "__main__":
    out = subprocess.check_output(
        ["bcdedit", "/enum", "firmware"], universal_newlines=True
    ).strip()
    entries = out.split("\n\n")
    entry_name_id_dict = {}
    for entry in entries:
        name = None
        id = None
        for line in entry.splitlines():
            if line.startswith("description"):
                name = line.split(maxsplit=2)[1]
            elif line.startswith("identifier"):
                id = line.split(maxsplit=2)[1]
        if name:
            entry_name_id_dict[name] = id

    menu = Menu(items=list(entry_name_id_dict.keys()))
    menu.exec()
    selected = menu.get_selected_item()

    uuid = entry_name_id_dict[selected]
    subprocess.check_call(["bcdedit", "/set", "{fwbootmgr}", "DEFAULT", uuid])
