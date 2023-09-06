import logging
import os
import tempfile
from zipfile import ZipFile

from _browser import open_url
from _script import get_all_scripts
from _shutil import set_clip, setup_logger

if __name__ == "__main__":
    setup_logger()

    user_script_export = os.path.join(tempfile.gettempdir(), "user_script_export.zip")

    with ZipFile(user_script_export, "w") as zip_object:
        for file in get_all_scripts():
            if file.lower().endswith(".user.js"):
                logging.info(f"Found user script file: {file}")

                zip_object.write(file, os.path.basename(file))

    logging.info(f"Create zip file for all user scripts: {user_script_export}")

    # Open Violentmonkey extension settings
    open_url(
        "chrome-extension://jinjaccalgkegednnccohejagnlnfdag/options/index.html#settings"
    )
    set_clip(user_script_export)
