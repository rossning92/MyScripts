from _shutil import *
from _term import *
from _audio import *

try_import('pyaudio')
import pyaudio
import wave


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
        self._pa = pyaudio.PyAudio()
        self.wavefile = self._prepare_file(self.fname, self.mode)
        self._stream = None

    def __enter__(self):
        return self

    def __exit__(self, exception, value, traceback):
        self.close()

    def record(self, duration):
        # Use a stream with no callback function in blocking mode
        self._stream = self._pa.open(format=pyaudio.paInt16,
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
        self._stream = self._pa.open(format=pyaudio.paInt16,
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
        self._pa.terminate()
        self.wavefile.close()

    def _prepare_file(self, fname, mode='wb'):
        wavefile = wave.open(fname, mode)
        wavefile.setnchannels(self.channels)
        wavefile.setsampwidth(self._pa.get_sample_size(pyaudio.paInt16))
        wavefile.setframerate(self.rate)
        return wavefile


class Player:
    def __init__(self, file_name):
        CHUNK = 1024

        wf = wave.open(file_name, 'rb')

        self.py_audio = pyaudio.PyAudio()

        # define callback (2)
        def callback(in_data, frame_count, time_info, status):
            data = wf.readframes(frame_count)
            return (data, pyaudio.paContinue)

        self.stream = self.py_audio.open(format=self.py_audio.get_format_from_width(wf.getsampwidth()),
                                         channels=wf.getnchannels(),
                                         rate=wf.getframerate(),
                                         output=True,
                                         stream_callback=callback)

        self.stream.start_stream()

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.py_audio.terminate()


if __name__ == '__main__':
    out_folder = expanduser('~/Desktop/{{_OUT_FOLDER}}')
    make_and_change_dir(out_folder)

    rec = Recorder(channels=2)

    recorder = None
    playback = None
    file_name = None
    while True:
        print2('SPACE - start / stop recording\n'
               'N     - Create noise profile\n')

        ch = getch()

        if ch == ' ':
            if recorder is None:
                file_name = 'AudioRecord_%s.wav' % get_time_str()

                recorder = rec.open(file_name, 'wb')
                recorder.start_recording()
                print2('Recording started.', color='green')

                if playback is not None:
                    playback.close()
                    playback = None

            else:
                recorder.stop_recording()
                recorder.close()
                recorder = None
                print2('Recording stopped. Saved as %s' % file_name, color='red')

                denoise(in_file=file_name)

                playback = Player(file_name)

        elif ch == 'd':
            if playback is not None:
                playback.close()
                playback = None

            if recorder is not None:
                recorder.close()
                recorder = None

            if os.path.exists(file_name):
                print2('File deleted: %s' % file_name, color='red')
                os.remove(file_name)

        elif ch == 'n':
            print2('Create noise profile. Please be quiet...', color='green')
            sleep(1)
            print('Start collecting.')
            with rec.open('noise.wav', 'wb') as r:
                r.start_recording()
                sleep(3)
                r.stop_recording()

            create_noise_profile('noise.wav')
            print('Noise profile created.')
