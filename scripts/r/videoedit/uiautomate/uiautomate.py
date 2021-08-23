import difflib
import glob
import os
import random
import time

import keyboard
import pyautogui
from _script import wt_wrap_args
from _shutil import exec_ahk, getch, set_clip
from videoedit.record_screen import CapturaScreenRecorder

INTERVAL_NEW_FILE = 1

root = os.path.dirname(os.path.abspath(__file__))

pyautogui.PAUSE = 0

recorder = CapturaScreenRecorder()


def set_window_pos(x, y, w, h):
    exec_ahk('#include <Window>\nSetWindowPos("A", %d, %d, %d, %d)\n' % (x, y, w, h))
    time.sleep(0.5)


def send_hotkey(modifier, key):
    pyautogui.hotkey(modifier, key)


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


def typing(s):
    for ch in s:
        if ch in ["\n", " ", "\t"]:
            pyautogui.write(ch)
            time.sleep(0.1)
        elif ch == " ":
            pyautogui.write(" ")
        else:
            time.sleep(random.uniform(0.02, 0.05))
            pyautogui.write(ch)


if __name__ == "__main__":
    while True:
        ch = getch()
        if ch == "d":
            files = sorted(glob.glob("**/*.rb", recursive=True))
            for i, f in enumerate(files):
                print("[%d] %s" % (i, f))

            i = int(input("index: "))

            exec_ahk("WinActivate, ahk_exe sonic-pi.exe")

            recorder.set_region([0, 0, 1920, 1080])

            name_no_ext = os.path.splitext(files[i])[0]

            if 1:
                # Record coding
                recorder.start_record()
                modify_code(files[i - 1] if i > 0 else None, files[i])
                time.sleep(2)
                recorder.stop_record()
                recorder.save_record(
                    "screencap/" + name_no_ext + "-code.mp4", overwrite=True
                )

            # Record playback
            recorder.start_record()
            pyautogui.hotkey("alt", "r")
            time.sleep(10)
            pyautogui.hotkey("alt", "s")
            time.sleep(1)
            recorder.stop_record()
            recorder.save_record(
                "screencap/" + name_no_ext + "-playback.mp4", overwrite=True
            )
            print("Done.")

        elif ch == "r":
            exec_ahk("WinActivate, ahk_exe sonic-pi.exe")

            # Record playback
            recorder.start_record()
            pyautogui.hotkey("alt", "r")
            time.sleep(30)
            pyautogui.hotkey("alt", "s")
            time.sleep(1)
            recorder.stop_record()
            f = input("file name (no ext) :")
            recorder.save_record("screencap/" + f + ".mp4", overwrite=True)
            print("Done.")


def sleep(secs):
    time.sleep(secs)


def run_commands(cmds):
    if type(cmds) != str:
        raise TypeError("cmds must be str")

    for cmd in cmds.splitlines():
        if cmd.startswith("!sleep"):
            secs = float(cmd.split(" ")[1])
            time.sleep(secs)
        else:
            typing(cmd + "\n")
