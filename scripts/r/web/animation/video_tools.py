from _shutil import *
import keyboard
from _term import *
import r.audio.recorder as rec

PROJ_DIR = r'C:\Data\how_to_make_video'
MD_FILE = r"{{_MD_FILE}}"


class RecorderWrapper:
    def __init__(self):
        self.file_saved = False
        self.is_recording = False
        self.recorder = rec.TerminalRecorder('record')

    def start_stop_screencap(self):
        keyboard.send('alt+F9')

        if not self.is_recording:
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

        self.is_recording = not self.is_recording

    def start_stop_recording(self):
        out_file = self.recorder.start_stop_record()
        if out_file is not None:
            clip = '<!-- record: %s -->' % out_file.replace('\\', '/')
            set_clip(clip)
            keyboard.send('ctrl+v')
            self.file_saved = True
        else:
            self.file_saved = False

    def delete_cur_file(self):
        self.recorder.delete_cur_file()
        if self.file_saved:
            keyboard.send('ctrl+z')
            self.file_saved = False


if __name__ == '__main__':
    wrapper = RecorderWrapper()

    cd(PROJ_DIR)

    keyboard.add_hotkey('`', wrapper.start_stop_screencap, suppress=True)

    keyboard.add_hotkey('F3', wrapper.start_stop_recording, suppress=True)
    keyboard.add_hotkey(
        'F5', wrapper.recorder.create_noise_profile, suppress=True)
    keyboard.add_hotkey('F4', wrapper.delete_cur_file, suppress=True)

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
