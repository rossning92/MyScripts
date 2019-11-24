from _shutil import *
from _term import *
from _audio import *
from _script import *

try_import('pyaudio')
import pyaudio
import wave

# TODO: cleanup by pa.terminate()
pa = pyaudio.PyAudio()

FILE_PREFIX = '{{_FILE_PREFIX}}' if '{{_FILE_PREFIX}}' else 'AudioRecord'

if 0:
    FILE_PREFIX = os.path.splitext(os.path.basename(get_files()[0]))[0]
    print2('FILE_PREFIX: %s' % FILE_PREFIX, color='green')


# set_variable('_FILE_PREFIX', FILE_PREFIX)


class Recorder(object):
    """
    Records in mono by default.
    """

    def __init__(self, channels=1, rate=44100, frames_per_buffer=1024):
        self.channels = channels
        self.rate = rate
        self.frames_per_buffer = frames_per_buffer

    def open(self, fname, mode='wb'):
        return RecordingFile(fname, mode, self.channels, self.rate,
                             self.frames_per_buffer)


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


def print_help():
    print2(
        'SPACE - Start / stop recording\n'
        'ENTER - Record next\n'
        'N     - Create noise profile\n'
        ', .   - Browse files\n'
    )


if __name__ == '__main__':
    out_folder = expanduser('~/Desktop/{{_OUT_FOLDER}}')
    make_and_change_dir(out_folder)

    rec = Recorder(channels=2)

    recorder = None
    playback = WavePlayer()
    cur_file_index = 0


    def get_audio_files():
        return list(glob.glob(FILE_PREFIX + '_*.wav'))


    def stop_all():
        global recorder

        playback.stop()

        if recorder is not None:
            recorder.close()
            recorder = None


    def playback_file(filename=None, offset=None):
        global cur_file_index

        files = get_audio_files()
        n = len(files)
        if n == 0:
            return

        if filename is not None:
            cur_file_index = files.index(filename)
            assert cur_file_index >= 0

        else:
            cur_file_index = max(min(cur_file_index + offset, len(files) - 1), 0)

        cur_file = files[cur_file_index]
        print(f'({cur_file_index+1}/{n}) {cur_file}')
        playback.play(cur_file)


    def delete_cur():
        global cur_file_index

        files = get_audio_files()
        if cur_file_index >= len(files):
            return

        file_name = files[cur_file_index]
        if os.path.exists(file_name):
            print2('File deleted: %s' % file_name, color='red')
            os.remove(file_name)


    print_help()

    cur_file_index = len(get_audio_files()) - 1
    file_name = None
    while True:
        ch = getch()

        if ch == 'h':
            print_help()

        elif ch == ' ':
            if recorder is None:
                playback.stop()

                files = get_audio_files()
                if cur_file_index < len(files) - 1:
                    prefix = os.path.splitext(files[cur_file_index])[0]
                else:
                    prefix = FILE_PREFIX

                file_name = get_audio_file_name(prefix=prefix)
                recorder = rec.open(file_name, 'wb')
                recorder.start_recording()
                print2('Recording started: %s' % file_name, color='green')

            else:
                recorder.stop_recording()
                recorder.close()
                recorder = None
                print2('Recording stopped.', color='red')

                denoise(in_file=file_name)

                playback_file(file_name)

        elif ch == '\r':
            stop_all()

            if file_name is not None:
                denoise(in_file=file_name)

            file_name = get_audio_file_name()
            recorder = rec.open(file_name, 'wb')
            recorder.start_recording()
            print2('Recording started: %s' % file_name, color='green')

        elif ch == 'd':
            stop_all()
            delete_cur()

        elif ch == 'n':
            stop_all()

            print2('Create noise profile. Please be quiet...', color='green')
            sleep(1)
            print('Start collecting.')
            with rec.open('noise.wav', 'wb') as r:
                r.start_recording()
                sleep(3)
                r.stop_recording()

            create_noise_profile('noise.wav')
            print('Noise profile created.')

        elif ch == ',':
            playback_file(offset=-1)

        elif ch == '.':
            playback_file(offset=1)
