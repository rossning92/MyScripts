import os
import shlex
import subprocess
import sys
import time
from typing import Literal


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


def _notify(message: str, icon: Literal["info", "error"] = "info"):
    if sys.platform == "win32":
        message_escaped = message.replace("'", "''")

        if icon == "error":
            icon_enum = "Error"
        else:
            icon_enum = "Information"

        subprocess.check_call(
            [
                "powershell",
                "-c",
                '[void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
                "$notify = New-Object System.Windows.Forms.NotifyIcon;"
                f"$notify.Icon = [System.Drawing.SystemIcons]::{icon_enum};"
                f"$notify.BalloonTipText = '{message_escaped}';"
                "$notify.Visible = $True;"
                "$notify.ShowBalloonTip(3000)",
            ]
        )


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
            _notify(
                f"Error on {' '.join(shlex.quote(arg) for arg in args)}", icon="error"
            )
            print("---")
            print("(exit code: %d)" % code)
            print("(duration: %.2f seconds)" % duration)
            print("(cmdline: %s)" % args)
            _getch()

    except KeyboardInterrupt:
        print("Ctrl-C")
