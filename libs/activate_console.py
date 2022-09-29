import ctypes

if __name__ == '__main__':
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    ctypes.windll.user32.SetForegroundWindow(hwnd)
