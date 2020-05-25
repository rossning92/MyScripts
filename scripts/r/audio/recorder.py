from _shutil import *
from _term import *
from _audio import *
from _script import *
from _gui import *

import pyaudio
import wave

if 1:
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    import postprocess

# TODO: cleanup by pa.terminate()
pa = pyaudio.PyAudio()

FILE_PREFIX = "record"


class RecordingFile(object):
    def __init__(self, fname, mode, channels, rate, frames_per_buffer):
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
        self._stream = pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
        )
        for _ in range(int(self.rate / self.frames_per_buffer * duration)):
            audio = self._stream.read(self.frames_per_buffer)
            self.wavefile.writeframes(audio)
        return None

    def start_recording(self):
        # Use a stream with a callback in non-blocking mode
        self._stream = pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.frames_per_buffer,
            stream_callback=self.get_callback(),
        )
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

    def _prepare_file(self, fname, mode="wb"):
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

    def open(self, fname, mode="wb"):
        return RecordingFile(
            fname, mode, self.channels, self.rate, self.frames_per_buffer
        )

    def record(self, file_name):
        self.recording_file = self.open(file_name, "wb")
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

        self.wavefile = wave.open(file_name, "rb")

        # define callback (2)
        def callback(in_data, frame_count, time_info, status):
            data = self.wavefile.readframes(frame_count)
            return (data, pyaudio.paContinue)

        self.stream = pa.open(
            format=pa.get_format_from_width(self.wavefile.getsampwidth()),
            channels=self.wavefile.getnchannels(),
            rate=self.wavefile.getframerate(),
            output=True,
            stream_callback=callback,
        )

        self.stream.start_stream()

    def stop(self):
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

        if self.wavefile is not None:
            self.wavefile.close()
            self.wavefile = None


def get_audio_file_name(prefix=FILE_PREFIX, postfix=".wav"):
    return "%s_%s%s" % (prefix, get_time_str(), postfix)


def get_audio_files(out_dir):
    return list(glob.glob(os.path.join(out_dir, FILE_PREFIX + "_*.wav")))


class TerminalRecorder:
    def __init__(self, out_dir=".", interactive=True):
        self.out_dir = out_dir
        self.recorder = WaveRecorder(channels=2)
        self.playback = WavePlayer()

        self.cur_file_name = None
        self.new_file_name = None
        self.interactive = interactive

        audio_files = get_audio_files(self.out_dir)
        if len(audio_files) > 0:
            self.cur_file_name = audio_files[-1]

    def getch(self):
        if self.interactive:
            return getch()
        else:
            return input().strip()

    def print_help(self):
        if self.interactive:
            print2(
                "SPACE - Start / stop recording\n"
                "R     - Start recording\n"
                "S     - Stop recording\n"
                "D     - Delete current\n"
                "N     - Create noise profile\n"
                ", .   - Go to prev / next\n"
                "[ ]   - Go to first / last\n"
                "E     - Output composed file\n"
                "O     - Output folder\n"
            )

    def _stop_all(self):
        self.playback.stop()
        self.recorder.stop()

    def _navigate_file(self, next=None, go_to_end=None):
        files = get_audio_files(self.out_dir)
        n = len(files)
        if n == 0:
            return

        if go_to_end is not None:
            if go_to_end:
                i = n - 1
            else:
                i = 0
        elif next is not None:
            try:
                i = files.index(self.cur_file_name)
            except ValueError:
                self.cur_file_name = None
                return

            if i > 0 and next == False:
                i -= 1
            elif i < n - 1 and next:
                i += 1

        self.cur_file_name = files[i]
        print(f"({i+1}/{n}) {self.cur_file_name}")

    def _play_cur_file(self):
        if self.cur_file_name:
            self.playback.play(self.cur_file_name)

    def delete_cur_file(self):
        self._stop_all()

        if not self.cur_file_name:
            return

        file_name = self.cur_file_name

        self._navigate_file(next=False)

        if os.path.exists(file_name):
            os.remove(file_name)
            print("delete file: %s" % file_name)

    def create_noise_profile(self):
        self._stop_all()

        print2("please be quiet...", color="green")
        sleep(1)
        print("start collecting noise profile")

        os.makedirs("tmp", exist_ok=True)
        with self.recorder.open("tmp/noise.wav", "wb") as r:
            r.start_recording()
            sleep(3)
            r.stop_recording()

        create_noise_profile("tmp/noise.wav")
        print("stop collection noise profile")

    def start_stop_record(self):
        """
        :return: new recorded file name when recording finishes otherwise None
        """

        if not self.recorder.is_recording():
            self.start_record()
            return None
        else:
            self.stop_record()
            return self.new_file_name

    def start_record(self):
        if self.recorder.is_recording():
            self.delete_cur_file()

        self.recorder.stop()
        self.playback.stop()

        if self.cur_file_name:
            self.new_file_name = get_next_file_name(self.cur_file_name)
        else:
            self.new_file_name = os.path.join(self.out_dir, FILE_PREFIX + "_001.wav")

        self.cur_file_name = self.new_file_name

        self.recorder.record(self.new_file_name)
        print("start recording: %s" % self.new_file_name)

    def stop_record(self):
        if self.recorder.is_recording():
            self.recorder.stop()
            print("stop recording")

            denoise(in_file=self.new_file_name)

            self._play_cur_file()

    def main_loop(self):
        self.print_help()

        while True:
            ch = self.getch()

            if ch == "h":
                self.print_help()

            elif ch == " ":
                self.start_stop_record()

            elif ch == "r":
                self.start_record()

            elif ch == "s":
                self.stop_record()

            elif ch == "d":
                self.delete_cur_file()

            elif ch == "n":
                self.create_noise_profile()

            elif ch == ",":
                self._stop_all()
                self._navigate_file(next=False)
                self._play_cur_file()

            elif ch == ".":
                self._stop_all()
                self._navigate_file(next=True)
                self._play_cur_file()

            elif ch == "[":
                self._stop_all()
                self._navigate_file(go_to_end=False)
                self._play_cur_file()

            elif ch == "]":
                self._stop_all()
                self._navigate_file(go_to_end=True)
                self._play_cur_file()

            elif ch == "e":
                self._stop_all()
                postprocess.create_final_vocal()

            elif ch == "o":
                start_process("explorer .")


if __name__ == "__main__":
    if "RECORD_OUT_DIR" in os.environ:
        out_dir = os.path.abspath(os.environ["RECORD_OUT_DIR"])
    else:
        out_dir = expanduser(r"{{_OUT_FOLDER}}")

    print("record out dir: %s" % out_dir)
    make_and_change_dir(out_dir)

    non_interactive = ("RECODER_INTERACTIVE" in os.environ) and (
        os.environ["RECODER_INTERACTIVE"] == "0"
    )

    TerminalRecorder(interactive=not non_interactive).main_loop()
