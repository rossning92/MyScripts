from _shutil import *
import keyboard
from _term import *
import r.audio.recorder as rec

PROJ_DIR = r'C:\Data\how_to_make_video'

is_recording = False

recorder = rec.TerminalRecorder(out_dir=os.path.join(PROJ_DIR, 'record'))


def start_stop_screencap():
    global is_recording

    keyboard.send('alt+F9')

    if not is_recording:
        print2('Start recording.')
        exec_ahk('''
        WinGet hwnd, ID, A
        Run %LOCALAPPDATA%\carnac\Carnac.exe
        Sleep 500
        WinActivate ahk_id %hwnd%
        ''')
    else:
        print2('stop recording.')
        call2('taskkill /f /im Carnac.exe 1>NUL 2>NUL', check=False)

    is_recording = not is_recording


def start_stop_recording():
    recorder.start_stop_record()


if __name__ == '__main__':

    keyboard.add_hotkey('`', start_stop_screencap, suppress=True)
    keyboard.add_hotkey('space', start_stop_recording, suppress=True)

    while True:
        new_file = wait_for_new_file(os.path.expandvars(
            r'%USERPROFILE%\Videos\Desktop\*.mp4'))

        activate_cur_terminal()
        file_name = input('input file name (no ext): ')
        if not file_name:
            print2('Discard %s.' % new_file, color='red')
            os.remove(new_file)
            continue

        file_name = slugify(file_name)
        file_name += '.mp4'
        print2('file saved: %s' % file_name, color='green')

        set_clip(file_name)

        os.rename(new_file, os.path.join(PROJ_DIR, file_name))
