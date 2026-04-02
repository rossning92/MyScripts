from utils.window import get_windows

if __name__ == "__main__":
    windows = get_windows()
    for window in windows:
        print(window.title)
