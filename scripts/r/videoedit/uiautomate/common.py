import difflib
import glob
import os
import random
import re
import time

import pyautogui
from _script import wrap_args_wt
from _shutil import exec_ahk, getch
from utils.clip import set_clip

INTERVAL_NEW_FILE = 1

root = os.path.dirname(os.path.abspath(__file__))

pyautogui.PAUSE = 0


def set_window_pos(x, y, w, h):
    exec_ahk('#include <Window>\nSetWindowPos("A", %d, %d, %d, %d)\n' % (x, y, w, h))
    time.sleep(0.5)


def send_hotkey(*args, **kwargs):
    pyautogui.hotkey(*args, **kwargs)


def press(keys):
    pyautogui.press(keys)


def modify_code(
    *files, on_new_line=None, on_load=None, on_complete=None, interval_new_line=0.1
):
    # Initialize with first file content
    with open(files[0], "r", encoding="utf-8", newline="\n") as f:
        s = f.read()
    set_clip(s)
    exec_ahk(
        """
    Send ^a
    Send ^v
    Send ^a
    Send {Left}
    """
    )

    def send_enter():
        set_clip("\n")
        pyautogui.hotkey("ctrl", "v")

    def send_char(ch):
        if ch == "\n":
            send_enter()
            time.sleep(0.1)
        elif ch == " ":
            pyautogui.write(" ")
        else:
            time.sleep(random.uniform(0.02, 0.05))
            pyautogui.write(ch)

    def send_line(line):
        # for ch in line:
        #     send_char(ch)
        set_clip(line)
        pyautogui.hotkey("ctrl", "v")
        if on_new_line:
            on_new_line()
        time.sleep(interval_new_line)

    last_mode = None
    last_pos = 0
    pos = 0
    prev_content = [x + "\n" for x in s.splitlines()]
    seek = True

    for file in files[1:]:
        time.sleep(INTERVAL_NEW_FILE)
        pos = 0

        with open(file, "r", encoding="utf-8", newline="\n") as f:
            content = [x + "\n" for x in f.read().splitlines()]

        for _, s in enumerate(difflib.ndiff(prev_content, content)):
            line = s[2:]
            mode = s[0]

            if mode != " " and pos != last_pos:
                print("move_to=%d  offset=%d" % (pos, pos - last_pos))
                for _ in range(abs(pos - last_pos)):
                    if pos > last_pos:
                        pyautogui.hotkey("down")
                    else:
                        pyautogui.hotkey("up")

                    time.sleep(0.01)

                for _ in range(15):
                    pyautogui.hotkey("ctrl", "down")
                    time.sleep(0.01)

                last_pos = pos

                if seek:
                    print("Seek finished...")
                    seek = False

                    if on_load:
                        on_load()

                    time.sleep(0.5)

            # HACK: always put add an empty line after
            # if last_mode == "+" and mode != "+":
            #     pyautogui.press("delete")
            # elif mode == "+" and last_mode != "+":
            #     send_enter()
            #     pyautogui.press("left")

            if mode == " ":
                pos += 1
                print("-", pos)
            elif mode == "-":
                pyautogui.hotkey("ctrl", "x")
                time.sleep(0.1)
                print(s.rstrip(), pos)
            elif mode == "+":
                send_line(line)
                pos += 1
                last_pos = pos
                print(s.rstrip(), pos)

            last_mode = mode

        prev_content = content

    if on_complete is not None:
        on_complete()


class TypingSound:
    def __init__(self) -> None:
        import simpleaudio as sa

        self.cur = 0
        self.waves = []

        for f in glob.glob(os.path.join(root, "typing_sound", "*.wav")):
            self.waves.append(sa.WaveObject.from_wave_file(f))

    def play(self):
        self.waves[self.cur].play()
        self.cur = (self.cur + 1) % len(self.waves)


_sound = None
# _sound = TypingSound()


def sleep_random(secs, sigma=None):
    if sigma is None:
        sigma = secs
    time.sleep(max(0, random.gauss(secs, sigma)))


def type_text(s, sound=False, no_sleep=False):
    for ch in s:
        if ch in [" ", "\t"]:
            if sound:
                _sound.play()
            if not no_sleep:
                sleep_random(0.1)
            pyautogui.write(ch)
            if not no_sleep:
                sleep_random(0.1)
        elif ch == "\n":
            if not no_sleep:
                sleep_random(0.3)
            pyautogui.write(ch)
            if not no_sleep:
                sleep_random(0.3)
        else:
            if not no_sleep:
                sleep_random(0.05)
            if sound:
                _sound.play()
            pyautogui.write(ch)


def sleep(secs):
    time.sleep(secs)


supported_keys = [
    "del",
    "down",
    "esc",
    "f1",
    "f10",
    "f11",
    "f12",
    "f2",
    "f3",
    "f4",
    "f5",
    "f6",
    "f7",
    "f8",
    "f9",
    "home",
    "insert",
    "left",
    "right",
    "up",
    "down",
    "pause",
    "pgdn",
    "pgup",
    "backspace",
]


def run_commands(cmd, sound=False, no_sleep=False):
    if type(cmd) != str:
        raise TypeError("cmd must be str")

    for c in re.split(r"((?<!\\)\{.*?(?<!\\)\})", cmd):
        if c.startswith("{"):
            c = c[1:-1]
            if c.startswith("sleep"):
                secs = float(c.split(" ")[1])
                time.sleep(secs)
            elif c.startswith("text"):
                text = c.lstrip("text ")
                pyautogui.write(text, interval=0)
            elif c in supported_keys:
                pyautogui.press(c)
                if not no_sleep:
                    sleep_random(0.1)
            elif re.match(r"^[!+^]*[0-9a-z]+(\*\d+)?$", c):
                arr = c.split("*")
                if len(arr) == 1:
                    hotkey = arr[0]
                    repeat = 1
                else:
                    hotkey = arr[0]
                    repeat = int(arr[1])

                for _ in range(repeat):
                    pyautogui.hotkey(
                        *hotkey.replace("+", "shift+")
                        .replace("!", "alt+")
                        .replace("^", "ctrl+")
                        .split("+")
                    )
                if not no_sleep:
                    sleep_random(0.1)
        else:
            c = c.replace("\\{", "{").replace("\\}", "}")
            type_text(c, sound=sound, no_sleep=no_sleep)
