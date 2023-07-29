#!/usr/bin/env python
import os

from _jsonedit import JsonEditWindow

if __name__ == "__main__":
    JsonEditWindow(
        os.path.join(os.environ["MY_DATA_DIR"], "proxy_settings.json"),
        default={"http_proxy": ""},
    ).exec()
