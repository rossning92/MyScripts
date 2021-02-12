import difflib
import keyboard
from _shutil import *
import pyautogui
import random
from r.web.animation.record_screen import CapturaScreenRecorder


NEXT_FILE_INTERVAL = 1
NEW_LINE_INTERVAL = 0.1

pyautogui.PAUSE = 0


def modify_code(*files):
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
    Sleep 500
    """
    )

    def send_enter():
        set_clip("\n")
        pyautogui.hotkey("ctrl", "v")

    def simulate_char(ch):
        if ch == "\n":
            send_enter()
            time.sleep(0.1)
        elif ch == " ":
            pyautogui.write(" ")
        else:
            time.sleep(random.uniform(0.02, 0.05) + 0.1)
            pyautogui.write(ch)

    def send_line(line):
        set_clip(line)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(NEW_LINE_INTERVAL)

    last_mode = None
    last_pos = 0
    pos = 0
    prev_content = [x + "\n" for x in s.splitlines()]

    for file in files[1:]:
        time.sleep(NEXT_FILE_INTERVAL)
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
                    time.sleep(0.1)
                last_pos = pos

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
                if 1:
                    send_line(line)
                else:
                    for ch in line:
                        simulate_char(ch)
                pos += 1
                last_pos = pos
                print(s.rstrip(), pos)

            last_mode = mode

        prev_content = content


if __name__ == "__main__":
    cd(r"C:\Users\Ross\Google Drive\KidslogicVideo\ep30\sonic-pi")

    recorder = CapturaScreenRecorder()

    while True:
        ch = getch()
        if ch == "d":
            files = sorted(glob.glob("**/*.rb", recursive=True))
            for i, f in enumerate(files):
                print("[%d] %s" % (i, f))

            i = input("index: ")
            i = int(i)

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
            sleep(10)
            pyautogui.hotkey("alt", "s")
            sleep(1)
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
            sleep(30)
            pyautogui.hotkey("alt", "s")
            sleep(1)
            recorder.stop_record()
            f = input("file name (no ext) :")
            recorder.save_record("screencap/" + f + ".mp4", overwrite=True)
            print("Done.")
