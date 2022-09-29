import ctypes
import threading
import tkinter


class MessageWindow:
    def __init__(self, text):
        self.text = text
        self.ev_close = threading.Event()
        self.thread = threading.Thread(target=self._thread_func)
        self.thread.start()

    def check_should_close(self):
        if self.ev_close.is_set():
            self.root.quit()
        self.root.after(100, self.check_should_close)

    def _thread_func(self):
        self.root = tkinter.Tk()
        self.root.lift()
        # self.root.protocol("WM_DELETE_WINDOW", self.callback)
        self.root.eval("tk::PlaceWindow . center")
        self.root.configure(bg="red")
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", 1)

        # self.root.attributes("-alpha", 1)
        # self.root.attributes("-transparentcolor", "#000000")
        # self.root.resizable(False, False)
        # self.set_clickthrough(self.root.winfo_id())

        label = tkinter.Label(self.root, text=self.text, font=("Arial", 12))
        label.config(bg="yellow")
        label.pack(padx=2, pady=2)

        self.root.after(100, self.check_should_close)
        self.root.mainloop()

    def close(self):
        self.ev_close.set()

    def set_clickthrough(self, hwnd):
        GWL_EXSTYLE = -20
        WS_EX_LAYERED = 0x80000
        WS_EX_TRANSPARENT = 0x00000020

        styles = ctypes.windll.user32.GetWindowLongA(hwnd, GWL_EXSTYLE)
        styles = WS_EX_LAYERED | WS_EX_TRANSPARENT
        ctypes.windll.user32.SetWindowLongA(hwnd, GWL_EXSTYLE, styles)
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, 255, 0x00000001)

    def wait(self):
        self.thread.join()
