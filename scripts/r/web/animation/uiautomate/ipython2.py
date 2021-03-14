import utils
from _script import wt_wrap_args
from _shutil import *
from r.web.animation.record_screen import recorder

root = os.path.dirname(os.path.abspath(__file__))


def open_wt_ipython():
    args = wt_wrap_args(
        ["ipython", "-i", os.path.join(root, "ipython_prompt.py")],
        title="ross@ross-desktop2: IPython",
        font_size=18,
        icon=(root + "/python.ico").replace("\\", "/"),
        opacity=0.9,
    )
    call_echo(args)


def record_wt_ipython(out):
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

    recorder.start_record()

    # Begin
    utils.simulate_typing("import numpy as np\n")
    time.sleep(2)

    utils.simulate_typing("np.zeros([4, 2])\n")
    time.sleep(2)

    utils.simulate_typing("np.random.randint([5, 5])\n")
    time.sleep(2)

    recorder.stop_record()
    recorder.save_record(out, overwrite=True)

    utils.send_hotkey("alt", "f4")
    exec_ahk("WinClose, show_overlay.ahk")


if __name__ == "__main__":
    cd("~/Desktop")
    record_wt_ipython(out="123.mp4")

