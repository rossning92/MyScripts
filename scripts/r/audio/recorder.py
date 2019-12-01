from _shutil import *
from _term import *
from _audio import *
from _script import *
from _gui import *

try_import('pyaudio')
import pyaudio
import wave

# TODO: cleanup by pa.terminate()
pa = pyaudio.PyAudio()

FILE_PREFIX = 'AudioRecord'


class RecordingFile(object):
    def __init__(self, fname, mode, channels,
                 rate, frames_per_buffer):
        self.fname = fname
        self.mode = mode
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record(self, duration):
        # Use a stream with no callback function in blocking mode
        self._stream = pa.open(format=pyaudio.paInt16,
                               channels=self.channels,
                               rate=self.rate,
                               input=True,
                               frames_per_buffer=self.frames_per_buffer)
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self):
        # Use a stream with a callback in non-blocking mode
        self._stream = pa.open(format=pyaudio.paInt16,
                               channels=self.channels,
                               rate=self.rate,
                               input=True,
                               frames_per_buffer=self.frames_per_buffer,
                               stream_callback=self.get_callback())
        self._stream.start_stream()
        return self

    def stop_recording(self):
        self._stream.stop_stream()
        return self

    def get_callback(self):
        def callback(in_data, frame_count, time_info, status):
            self.wavefile.writeframes(in_data)
            return in_data, pyaudio.paContinue

        return callback

    def close(self):
        self._stream.close()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile


class WaveRecorder(object):
    """
    Records in mono by default.
    """

    def __init__(self, channels=1, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer

        self.recording_file = None

    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.channels, self.rate,
                             self.frames_per_buffer)

    def record(self, file_name):
        self.recording_file = self.open(file_name, 'wb')
        self.recording_file.start_recording()

    def stop(self):
        if self.recording_file is not None:
            self.recording_file.stop_recording()
            self.recording_file.close()
            self.recording_file = None

    def is_recording(self):
        return self.recording_file is not None


class WavePlayer:
    def __init__(self):
        self.wavefile = None
        self.stream = None

    def play(self, file_name):
        self.stop()

        self.wavefile = wave.open(file_name, 'rb')

        # define callback (2)
        def callback(in_data, frame_count, time_info, status):
            data = self.wavefile.readframes(frame_count)
            return (data, pyaudio.paContinue)

        self.stream = pa.open(format=pa.get_format_from_width(self.wavefile.getsampwidth()),
                              channels=self.wavefile.getnchannels(),
                              rate=self.wavefile.getframerate(),
                              output=True,
                              stream_callback=callback)

        self.stream.start_stream()

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self.wavefile is not None:
            self.wavefile.close()
            self.wavefile = None


def get_audio_file_name(prefix=FILE_PREFIX, postfix='.wav'):
    return '%s_%s%s' % (prefix, get_time_str(), postfix)


def get_audio_files():
    return list(glob.glob(FILE_PREFIX + '_*.wav'))


class MyFancyRecorder:
    def __init__(self):
        self.rec = WaveRecorder(channels=2)
        self.playback = WavePlayer()
        self.cur_file_index = len(get_audio_files())
        self.prefix = FILE_PREFIX

    def print_help(self):
        print2(
            'SPACE - Start / stop recording\n'
            'ENTER - Record next\n'
            'N     - Create noise profile\n'
            ', .   - Browse files\n'
            'O     - Output composed file\n'
        )

    def stop_all(self):
        self.playback.stop()
        self.rec.stop()

    def set_cur_file(self, filename=None, offset=None):
        files = get_audio_files()
        if filename is not None:
            files = get_audio_files()
            self.cur_file_index = files.index(filename)
            assert self.cur_file_index >= 0
        else:
            assert offset is not None
            self.cur_file_index = max(min(self.cur_file_index + offset, len(files) - 1), 0)

    def play_file(self, filename=None, offset=None, set_prefix=False):
        files = get_audio_files()
        n = len(files)
        if n == 0:
            return

        self.set_cur_file(filename, offset)

        cur_file = files[self.cur_file_index]
        print(f'({self.cur_file_index+1}/{n}) {cur_file}')
        self.playback.play(cur_file)

        if set_prefix:
            if self.cur_file_index < len(files) - 1:
                self.prefix = os.path.splitext(files[self.cur_file_index])[0]
            else:
                self.prefix = FILE_PREFIX

    def delete_cur_file(self):
        files = get_audio_files()
        if self.cur_file_index >= len(files):
            return

        file_name = files[self.cur_file_index]
        if os.path.exists(file_name):
            print2('File deleted: %s' % file_name, color='red')
            os.remove(file_name)

    def main_loop(self):
        self.print_help()

        file_name = None
        while True:
            ch = getch()

            if ch == 'h':
                self.print_help()

            elif ch == ' ':
                if not self.rec.is_recording():
                    self.rec.stop()
                    self.playback.stop()

                    file_name = get_audio_file_name(prefix=self.prefix)
                    self.rec.record(file_name)
                    self.set_cur_file(file_name)
                    print2('Recording started: %s' % file_name, color='green')

                else:
                    self.rec.stop()
                    print2('Recording stopped.', color='red')

                    denoise(in_file=file_name)

                    self.play_file(file_name)

            elif ch == 'd':
                self.stop_all()
                self.delete_cur_file()

            elif ch == 'n':
                self.stop_all()

                print2('Create noise profile. Please be quiet...', color='green')
                sleep(1)
                print('Start collecting.')
                with self.rec.open('noise.wav', 'wb') as r:
                    r.start_recording()
                    sleep(3)
                    r.stop_recording()

                create_noise_profile('noise.wav')
                print('Noise profile created.')

            elif ch == ',':
                self.play_file(offset=-1, set_prefix=True)

            elif ch == '.':
                self.play_file(offset=1, set_prefix=True)

            elif ch == 'o':
                self.stop_all()
                run_script('/r/audio/jumpcutter')


from PyQt5.QtMultimedia import *


class RecorderGui(QDialog):
    def __init__(self):
        super().__init__()

        self.cur_file_index = 0
        self.audio_files = []

        # Widgets
        self.setLayout(QVBoxLayout())

        self.label = QLabel()
        self.label.setText('yoyo')
        self.layout().addWidget(self.label)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.lw_selection_changed)
        self.layout().addWidget(self.list_widget)

        # Media player
        self.playlist = None

        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.qmp_state_changed)

        self.update_audio_files()

        self.resize(500, 500)

    def set_cur_file(self, offset):
        self.cur_file_index = max(min(self.cur_file_index + offset, len(self.audio_files) - 1), 0)

        self.list_widget.blockSignals(True)
        self.list_widget.setCurrentRow(self.cur_file_index)
        self.list_widget.blockSignals(False)

    def lw_selection_changed(self):
        self.cur_file_index = self.list_widget.currentRow()

        self.play_cur_file()

    def play_cur_file(self):
        self.player.blockSignals(True)

        self.playlist = QMediaPlaylist()
        self.playlist.addMedia(QMediaContent(QUrl.fromLocalFile(self.audio_files[self.cur_file_index])))
        self.player.setPlaylist(self.playlist)
        self.player.stop()
        self.player.play()

        self.player.blockSignals(False)

    def update_audio_files(self):
        self.audio_files = get_audio_files()
        self.list_widget.clear()
        for f in self.audio_files:
            self.list_widget.addItem(f)

    def qmp_state_changed(self):
        if self.player.state() == QMediaPlayer.StoppedState:
            print('end')
            self.set_cur_file(offset=1)
            self.play_cur_file()


if __name__ == '__main__':
    out_folder = expanduser(r'{{_OUT_FOLDER}}')
    make_and_change_dir(out_folder)

    # d = RecorderGui()
    # d.exec()

    MyFancyRecorder().main_loop()
