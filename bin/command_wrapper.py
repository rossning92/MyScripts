import os
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


def _format_seconds(seconds: float) -> str:
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    result = f"{minutes:02}:{remaining_seconds:02.0f}"
    return result


if __name__ == "__main__":
    close_on_exit = int(os.environ.get("CMDW_CLOSE_ON_EXIT", "1"))
    window_title = os.environ.get("CMDW_WINDOW_TITLE")

    start_time = time.time()
    args = sys.argv[1:]
    try:
        code = subprocess.call(args)

        end_time = time.time()
        has_error = code != 0
        duration = end_time - start_time
        keep_terminal_on = not close_on_exit
        if duration > 10 or has_error:
            _notify(
                f"{window_title} finished in {_format_seconds(duration)}, exit code {code}",
                icon="info" if code == 0 else "error",
            )
        if has_error or keep_terminal_on:
            print("---")
            print("(exit code: %d)" % code)
            print(f"(duration: {_format_seconds(duration)} seconds)")
            print("(cmdline: %s)" % args)
            _getch()

    except KeyboardInterrupt:
        print("Ctrl-C")
