import ctypes
import sys

_console_color_initialized = False


def printc(msg, color="yellow", end="\n"):
    # https://gist.github.com/dominikwilkowski/60eed2ea722183769d586c76f22098dd
    # ANSI escape codes for colors
    COLOR_MAP = {
        "gray": "\u001b[90m",
        "blue": "\u001b[34m",
        "cyan": "\u001b[36m",
        "green": "\u001b[32m",
        "magenta": "\u001b[35m",
        "red": "\u001b[31m",
        "RED": "\u001b[41m",
        "white": "\u001b[37m",
        "yellow": "\u001b[33m",
        "YELLOW": "\u001b[43m",
    }
    RESET = "\033[0m"

    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    global _console_color_initialized
    if not _console_color_initialized:
        if sys.platform == "win32":
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        _console_color_initialized = True

    if not isinstance(msg, str):
        msg = str(msg)
    print(COLOR_MAP[color] + msg + RESET, end=end, flush=True)
