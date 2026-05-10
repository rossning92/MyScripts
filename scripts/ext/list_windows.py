import sys
import io

from utils.window import get_windows

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    windows = get_windows()
    for window in windows:
        print(window.title)
