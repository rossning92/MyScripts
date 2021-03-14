from _script import wt_wrap_args
from _shutil import *
from r.web.animation.record_screen import recorder
from .uiautomate import *

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
    if os.path.exists(file):
        return file

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

    return file

