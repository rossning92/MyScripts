import sys
from time import sleep


def getch(timeout=-1.0):
    """Get a single character from user input.

    Returns:
        str or None: The character read, or None if the operation times out.
    Raises:
        KeyboardInterrupt: If the user interrupts the input with Ctrl+C.
    """

    if sys.platform == "win32":
        import msvcrt

        time_elapsed = 0.0
        if timeout > 0.0:
            while not msvcrt.kbhit() and time_elapsed < timeout:
                sleep(0.1)
                time_elapsed += 0.1
            if time_elapsed < timeout:
                ch = msvcrt.getch().decode(errors="replace")
            else:
                ch = None
        else:
            ch = msvcrt.getch().decode(errors="replace")

    else:
        import select
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            if timeout > 0.0:
                rlist, _, _ = select.select([sys.stdin], [], [], timeout)
                if rlist:
                    ch = sys.stdin.read(1)
                else:
                    ch = None
            else:
                ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    if ch is not None and ord(ch) == 3:
        raise KeyboardInterrupt
    return ch
