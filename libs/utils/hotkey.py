import sys
from typing import Callable


def register_global_hotkey(key_name: str, on_hotkey: Callable[[], bool]):
    if sys.platform == "linux":
        from Xlib import XK, X, display

        # Connect to X server
        disp = display.Display()
        root = disp.screen().root

        # Define the hotkey
        mods = 0
        keysym = XK.string_to_keysym(key_name)
        keycode = disp.keysym_to_keycode(keysym)

        # Grab the key globally (root window)
        root.grab_key(keycode, mods, True, X.GrabModeAsync, X.GrabModeAsync)

        while True:
            event = root.display.next_event()
            if event.type == X.KeyPress:
                if event.detail == keycode and event.state == mods:
                    if on_hotkey():
                        return
    else:
        from pynput import keyboard

        key_attr = key_name.lower()
        if hasattr(keyboard.Key, key_attr):
            hotkey = getattr(keyboard.Key, key_attr)
        else:
            hotkey = keyboard.KeyCode.from_char(key_name.lower())

        def on_press(key):
            matches_key = key == hotkey
            if not matches_key and isinstance(hotkey, keyboard.KeyCode):
                matches_key = getattr(key, "char", None) == hotkey.char
            if matches_key:
                if on_hotkey():
                    return False

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()
