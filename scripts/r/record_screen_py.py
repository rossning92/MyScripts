import time

import numpy
from _video import *
from _shutil import *

try_import('mss')
try_import('keyboard')
import mss
import keyboard


def get_images():
    i = 0
    with mss.mss() as sct:
        # Part of the screen to capture

        x, y, w, h = get_active_window_rect()
        monitor = {'left': x, 'top': y, 'width': w, 'height': h}

        while 'Screen capturing':
            last_time = time.time()

            # Get raw pixels from the screen, save it to a Numpy array
            img = numpy.array(sct.grab(monitor))

            print(img.shape)
            yield img

            print('fps: {0}'.format(1 / (time.time() - last_time)))

            i += 1

            if i > 200:
                return


def get_active_window_rect():
    import win32gui

    hwnd = win32gui.GetForegroundWindow()

    if False:
        rect = win32gui.GetWindowRect(hwnd)
        x = rect[0]
        y = rect[1]
        w = rect[2] - x
        h = rect[3] - y
        print("Window %s:" % win32gui.GetWindowText(hwnd))
        print("\tLocation: (%d, %d)" % (x, y))
        print("\t    Size: (%d, %d)" % (w, h))
        return x, y, w, h
    else:
        _left, _top, _right, _bottom = win32gui.GetClientRect(hwnd)
        left, top = win32gui.ClientToScreen(hwnd, (_left, _top))
        right, bottom = win32gui.ClientToScreen(hwnd, (_right, _bottom))
        return left, top, right - left, bottom - top


def record():
    make_video(get_images(), format='rgb32', fps=60, out_file='Record_%s.mp4' % get_time_str())


chdir(expanduser('~/Desktop'))
keyboard.add_hotkey('f7', lambda: record())
while True:
    sleep(1)
