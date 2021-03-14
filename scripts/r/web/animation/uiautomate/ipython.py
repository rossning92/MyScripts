from _script import wt_wrap_args
from _shutil import *
from r.web.animation.record_screen import recorder
from utils import *

root = os.path.dirname(os.path.abspath(__file__))


def open_wt_ipython():
    args = wt_wrap_args(
        ["ipython", "-i", os.path.join(root, "_ipython_prompt.py")],
        title="ross@ross-desktop2: IPython",
        font_size=18,
        icon=(root + "/python.ico").replace("\\", "/"),
        opacity=0.9,
    )
    call_echo(args)


def record_ipython(file, func):
    run_ahk(os.path.join(root, "show_overlay.ahk"))
    time.sleep(2)

    open_wt_ipython()
    time.sleep(2)

    exec_ahk(
        """
        #include <Window>
        WinWaitActive, ahk_exe WindowsTerminal.exe
        SetWindowPos("A", 240, 125, 1440, 810)
        """
    )
    sleep(0.5)

    recorder.set_region((0, 0, 1920, 1080))

    recorder.start_record(file)

    func()

    sleep(2)
    recorder.stop_record()

    send_hotkey("alt", "f4")
    exec_ahk("WinClose, show_overlay.ahk")


if __name__ == "__main__":
    cd(r"C:\Users\Ross\Google Drive\KidslogicVideo\ep36\screencap")

    record_ipython("np-linspace.mp4", lambda: typing("np.linspace(0, 1, 5)\n"))

    # recorder.start_record("import-numpy.mp4")
    # utils.simulate_typing("import numpy as np\n")
    # sleep(2)
    # recorder.stop_record()

    # recorder.start_record("np-array.mp4")
    # utils.simulate_typing("np.array([1, 2, 3, 4, 5])\n")
    # sleep(2)
    # recorder.stop_record()

    # recorder.start_record("np-zeros.mp4")
    # utils.simulate_typing("np.zeros( (3, 2) )\n")
    # sleep(2)
    # recorder.stop_record()

    # recorder.start_record("array-shape.mp4")
    # utils.simulate_typing("a = np.zeros( (3, 2) )\n")
    # utils.simulate_typing("a.shape\n")
    # sleep(2)
    # recorder.stop_record()

    # recorder.start_record("np-arange.mp4")
    # utils.simulate_typing("np.arange(3, 7)\n")
    # sleep(2)
    # recorder.stop_record()

