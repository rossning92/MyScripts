import os
import subprocess
import sys
import time


def _getch():
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getch().decode(errors="replace")

    else:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    if ch is not None and ord(ch) == 3:
        raise KeyboardInterrupt
    return ch


if __name__ == "__main__":
    close_on_exit = int(os.environ.get("CLOSE_ON_EXIT", "1"))

    start_time = time.time()
    args = sys.argv[1:]
    try:
        code = subprocess.call(args)

        end_time = time.time()
        has_error = code != 0
        duration = end_time - start_time
        keep_terminal_on = not close_on_exit
        if has_error or keep_terminal_on:
            print("---")
            print("(exit code: %d)" % code)
            print("(duration: %.2f seconds)" % duration)
            print("(cmdline: %s)" % args)
            _getch()

    except KeyboardInterrupt:
        print("Ctrl-C")
