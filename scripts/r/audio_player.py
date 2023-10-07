import glob
import os
import signal
import subprocess
import sys

from _shutil import fnull
from utils.menu import Menu

EXTENSIONS = {".wav", ".mp3", ".mid", ".ogg"}

folder = os.environ["AUDIO_DIR"]
files = list(glob.glob(os.path.join(folder, "**", "*"), recursive=True))
files = [x for x in files if os.path.isfile(x)]
files = [x.replace(folder + os.path.sep, "").replace("\\", "/") for x in files]
files = [x for x in files if os.path.splitext(x)[1] in EXTENSIONS]


def play(file):
    if not hasattr(play, "ps"):
        play.ps = None

    if play.ps is not None:
        if sys.platform == "win32":
            subprocess.call("taskkill /f /t /pid %d >nul" % play.ps.pid, shell=True)
            # ctypes.windll.kernel32.TerminateProcess(int(play.ps.pid), -1)
            # ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, play.ps.pid)
        else:
            play.ps.send_signal(signal.CTRL_C_EVENT)

        play.ps = None

    if file.endswith(".mid"):
        import pygame

        try:
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()
        except:
            pygame.init()
            pygame.mixer.music.load(file)
            pygame.mixer.music.play()

    else:
        FNULL = fnull()
        play.ps = subprocess.Popen(
            ["ffplay", "-nodisp", file], stdout=FNULL, stderr=FNULL
        )


class AudioFileMenu(Menu):
    def on_item_selected(self):
        i = self.get_selected_index()
        f = os.path.join(folder, files[i])
        play(f)


w = AudioFileMenu(items=files)
w.exec()
