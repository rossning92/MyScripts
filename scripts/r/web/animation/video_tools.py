from _shutil import *
import keyboard
from _term import *

PROJ_DIR = r'C:\Data\how_to_make_video'

is_recording = False


def toggle_recording():
    global is_recording

    keyboard.send('alt+F9')

    if not is_recording:
        print2('Start recording.')
        start_process(os.path.expandvars(r'%LOCALAPPDATA%\carnac\Carnac.exe'))
    else:
        print2('stop recording.')
        call2('taskkill /f /im Carnac.exe 1>NUL 2>NUL', check=False)

    is_recording = not is_recording


keyboard.add_hotkey('`', toggle_recording, suppress=True)


while True:
    new_file = wait_for_new_file(os.path.expandvars(
        r'%USERPROFILE%\Videos\Desktop\*.mp4'))

    activate_cur_terminal()
    file_name = input('input file name (no ext): ')
    file_name = slugify(file_name)
    file_name += '.mp4'
    print2('file saved: %s' % file_name, color='green')
    
    set_clip(file_name)

    os.rename(new_file, os.path.join(PROJ_DIR, file_name))
    