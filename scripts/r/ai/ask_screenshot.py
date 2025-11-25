import os
import tempfile

from _image import crop_image_interactive
from ai.chat_menu import ChatMenu
from PIL import ImageGrab


def screenshot(file_path: str):
    img = ImageGrab.grab()
    img.save(file_path)


def _main():
    try:
        screenshot_file = tempfile.mktemp(suffix=".png")
        screenshot(screenshot_file)
        crop_image_interactive(screenshot_file)
        chat = ChatMenu(context=screenshot_file)
        chat.exec()
    finally:
        os.remove(screenshot_file)


if __name__ == "__main__":
    _main()
