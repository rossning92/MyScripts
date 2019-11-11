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


class Player:
    def __init__(self, file_name):
        CHUNK = 1024

        wf = wave.open(file_name, 'rb')

        # define callback (2)
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        self.stream = pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                              channels=wf.getnchannels(),
                              rate=wf.getframerate(),
                              output=True,
                              stream_callback=callback)

        self.stream.start_stream()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()


def get_audio_file_name(prefix=FILE_PREFIX, postfix='.wav'):
    return '%s_%s%s' % (prefix, get_time_str(), postfix)


if __name__ == '__main__':
    out_folder = expanduser('~/Desktop/{{_OUT_FOLDER}}')
    make_and_change_dir(out_folder)

    rec = Recorder(channels=2)

    recorder = None
    playback = None


    def stop_all():
        global playback, recorder

        if playback is not None:
            playback.close()
            playback = None

        if recorder is not None:
            recorder.close()
            recorder = None


    file_name = None
    while True:
        print2(
            'SPACE - Start / Stop recording\n'
            'ENTER - Record Next\n'
            'N     - Create noise profile\n'
            'L     - List files\n'
        )

        ch = getch()
        print(ch)

        if ch == ' ':
            if recorder is None:
                if playback is not None:
                    playback.close()
                    playback = None

                file_name = get_audio_file_name()
                recorder = rec.open(file_name, 'wb')
                recorder.start_recording()
                print2('Recording started: %s' % file_name, color='green')

            else:
                recorder.stop_recording()
                recorder.close()
                recorder = None
                print2('Recording stopped.', color='red')

                denoise(in_file=file_name)

                playback = Player(file_name)

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

            if os.path.exists(file_name):
                print2('File deleted: %s' % file_name, color='red')
                os.remove(file_name)

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
