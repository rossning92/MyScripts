import os
import shutil
import sys
from subprocess import check_call

from _script import run_script


def create_noise_profile(in_file):
    os.makedirs("tmp", exist_ok=True)
    check_call(["sox", in_file, "-n", "noiseprof", "tmp/noise.prof"])


def denoise(in_file, out_file=None):
    os.makedirs("tmp", exist_ok=True)
    if os.path.exists("tmp/noise.prof"):
        if out_file is None:
            tmp_file = in_file + ".denoise.wav"
        else:
            tmp_file = out_file

        print("De-noising %s..." % in_file)
        check_call(["sox", in_file, tmp_file, "noisered", "tmp/noise.prof", "0.21"])

        if out_file is None:
            shutil.copyfile(tmp_file, in_file)
            os.remove(tmp_file)

    else:
        print("WARNING: Skip noise reduction, profile does not exist.")


def concat_audio(audio_files, silence_secs, out_file, channels=2):
    if silence_secs > 0:
        os.makedirs("tmp", exist_ok=True)
        check_call(
            [
                "sox",
                "-n",
                "-c",
                str(channels),
                "tmp/silence.wav",
                "trim",
                "0.0",
                str(silence_secs),
            ]
        )
        with_silence = []
        for idx, file in enumerate(audio_files):
            if idx > 0:
                with_silence.append("tmp/silence.wav")
            with_silence.append(file)
        audio_files = with_silence
    cmd = ["sox", *audio_files, out_file]

    print("Output %s" % out_file)
    check_call(cmd)


def set_mic_volume(volume: float = 0.5):
    if not isinstance(volume, (int, float)):
        raise ValueError("Volume must be numeric")
    if volume < 0.0 or volume > 1.0:
        raise ValueError("Volume must be between 0 and 1")
    if sys.platform == "linux":
        percent = max(0, min(100, int(volume * 100)))
        check_call(["pactl", "set-source-volume", "@DEFAULT_SOURCE@", f"{percent}%"])
    elif sys.platform == "win32":
        run_script("r/audio/set_mic_volume.ps1")
    else:
        raise NotImplementedError()
