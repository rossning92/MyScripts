import datetime
import glob
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from typing import Optional

from _shutil import (
    get_hash,
    get_home_path,
    getch,
    mkdir,
    print2,
    sleep,
)
from audio.postprocess import process_audio_file
from utils.audio import concat_audio, create_noise_profile, denoise, set_mic_volume
from utils.menu.filemenu import FileMenu

FILE_PREFIX = "record"
RECORD_FILE_TYPE = "wav"


class SoxRecording:
    def __init__(self):
        self._sox_proc: Optional[subprocess.Popen[bytes]] = None

    def start_recording(self, fname: str) -> None:
        if self._sox_proc is None:
            self._sox_proc = subprocess.Popen(
                [
                    "rec",
                    "--buffer",
                    "256",
                    "--input-buffer",
                    "256",
                    "--no-show-progress",
                    "-V1",
                    fname,
                ]
            )

    def stop_recording(self) -> None:
        if self._sox_proc is not None:
            self._sox_proc.send_signal(signal.SIGINT)
            self._sox_proc.wait()
            self._sox_proc = None

    def is_recording(self) -> bool:
        return self._sox_proc is not None and self._sox_proc.poll() is None


class SoxPlayback:
    def __init__(self):
        self.ps = None

    def play(self, file):
        if self.ps is None:
            self.ps = subprocess.Popen(["play", "-q", file])

    def stop(self):
        if self.ps is not None:
            if sys.platform == "win32":
                subprocess.call("TASKKILL /F /T /PID %d >NUL" % self.ps.pid, shell=True)
            else:
                self.ps.send_signal(signal.SIGTERM)
            self.ps = None


def get_audio_files(folder="."):
    files = glob.glob(os.path.join(folder, FILE_PREFIX + "_*." + RECORD_FILE_TYPE))
    files.sort(key=os.path.getmtime)
    return files


def create_final_vocal():
    mkdir("tmp")
    mkdir("out")

    audio_files = get_audio_files()
    if len(audio_files) == 0:
        raise Exception("No audio files for concatenation.")

    processed_files = []
    for f in audio_files:
        out_file = process_audio_file(f)
        processed_files.append(out_file)

    out_file = "out/concat.wav"
    concat_audio(processed_files, 0, out_file=out_file, channels=1)
    return out_file


class TerminalRecorder:
    def __init__(self, out_dir="", interactive=True):
        self.out_dir = out_dir
        self.recording = SoxRecording()
        self.playback = SoxPlayback()

        self.cur_file_name = None
        self.interactive = interactive

        fd, path = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        self.tmp_wav_file = path

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
                "r     - Start recording\n"
                "s     - Stop recording\n"
                "d     - Delete current\n"
                "n     - Create noise profile\n"
                "N     - Remove noise profile\n"
                ", .   - Go to prev / next\n"
                "[ ]   - Go to first / last\n"
                "e     - Output composed file\n"
                "o     - Output folder\n"
            )

    def _stop_all(self):
        self.playback.stop()
        self.recording.stop_recording()

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
        elif next is not None and self.cur_file_name is not None:
            try:
                i = files.index(self.cur_file_name)
            except ValueError:
                self.cur_file_name = None
                return

            if i > 0 and not next:
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
            print("LOG: file deleted: %s" % file_name, flush=True)

    def create_noise_profile(self):
        self._stop_all()

        print("LOG: please be quiet", flush=True)
        sleep(1)
        print("LOG: start collecting noise profile", flush=True)

        os.makedirs("tmp", exist_ok=True)
        noise_recording = SoxRecording()
        noise_recording.start_recording("tmp/noise.wav")
        sleep(3)
        noise_recording.stop_recording()

        create_noise_profile("tmp/noise.wav")
        print("LOG: stop collecting noise profile", flush=True)

    def remove_noise_profile(self):
        if os.path.exists("tmp/noise.wav"):
            print("LOG: noise profile removed")
            os.remove("tmp/noise.wav")

    def start_record(self):
        if self.recording.is_recording():
            self.delete_cur_file()
            self.recording.stop_recording()

        self.playback.stop()

        self.cur_file_name = os.path.join(
            self.out_dir,
            "%s_%s.%s"
            % (
                FILE_PREFIX,
                get_hash(repr(datetime.datetime.now()), digit=8),
                RECORD_FILE_TYPE,
            ),
        )

        self.recording.start_recording(self.tmp_wav_file)

        print("LOG: start recording: %s" % self.cur_file_name, flush=True)

    def stop_record(self):
        self.playback.stop()

        if not self.cur_file_name:
            return

        if self.recording.is_recording():
            print("LOG: stop recording: %s" % self.cur_file_name, flush=True)
            self.recording.stop_recording()

            denoise(in_file=self.tmp_wav_file)

            if RECORD_FILE_TYPE == "wav":
                shutil.copyfile(self.tmp_wav_file, self.cur_file_name)
            else:
                subprocess.check_call(
                    [
                        "sox",
                        self.tmp_wav_file,
                        "--channel",
                        "1",
                        # Compression level (0-10). The higher number, the
                        # better quality.
                        "-C",
                        "10",
                        self.cur_file_name,
                    ]
                )
            os.remove(self.tmp_wav_file)

            self.playback.play(self.cur_file_name)

            # Don't play what's recorded.
            # self._play_cur_file()

    def main_loop(self):
        self.print_help()

        while True:
            ch = self.getch()

            if ch == "h":
                self.print_help()

            elif ch == "r":
                self.start_record()

            elif ch == "s":
                self.stop_record()

            elif ch == "d":
                self.delete_cur_file()

            elif ch == "n":
                set_mic_volume()
                self.create_noise_profile()

            elif ch == "N":
                self.remove_noise_profile()

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
                out_file = create_final_vocal()
                self.playback.play(out_file)

            elif ch == "o":
                FileMenu(
                    goto=os.getcwd(),
                    prompt="All recordings",
                    allow_cd=False,
                ).exec()

            elif ch == "q":
                sys.exit(0)


if __name__ == "__main__":
    out_dir = os.environ.get("RECORD_OUT_DIR")
    if not out_dir:
        out_dir = os.path.join(get_home_path(), "Recordings")

    out_dir = os.path.abspath(out_dir)
    print("record out dir: %s" % out_dir)
    os.makedirs(out_dir, exist_ok=True)
    os.chdir(out_dir)

    non_interactive = ("RECORD_INTERACTIVE" in os.environ) and (
        os.environ["RECORD_INTERACTIVE"] == "0"
    )

    set_mic_volume()
    TerminalRecorder(interactive=not non_interactive).main_loop()
