#!/usr/bin/env python
import os

from utils.menu.jsoneditmenu import JsonEditMenu

if __name__ == "__main__":
    JsonEditMenu(
        os.path.join(os.environ["MY_DATA_DIR"], "proxy_settings.json"),
        default={"http_proxy": ""},
    ).exec()
