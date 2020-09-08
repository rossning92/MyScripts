from _shutil import *
from _term import *
import subprocess

folder = r"C:\Users\Ross\Downloads\KSHMR"
files = list(glob.glob(os.path.join(folder, "**", "*"), recursive=True))
files = [x for x in files if os.path.isfile(x)]
files = [x.replace(folder + os.path.sep, "").replace("\\", "/") for x in files]


def play(file):
    if not hasattr(play, "ps"):
        play.ps = None

    if play.ps is not None:
        # play.ps.terminate()
        # play.ps.send_signal(signal.SIGINT)
        ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, play.ps.pid)
        play.ps = None

    FNULL = fnull()
    play.ps = subprocess.Popen(
        ["ffplay", "-nodisp", "-nodisp", file], stdout=FNULL, stderr=FNULL
    )


class MusicBrowseWindow(SearchWindow):
    def on_item_selected(self):
        i = self.get_selected_index()
        f = os.path.join(folder, files[i])
        play(f)


w = MusicBrowseWindow(items=files)
