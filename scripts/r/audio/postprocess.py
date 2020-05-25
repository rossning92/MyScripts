from scipy.io import wavfile
from _shutil import *
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from _audio import *

ALWAYS_GENERATE = False

BORDER_IGNORE = 0.1
LOUDNESS_DB = -14

COMPRESSOR_ATTACK = 0.0
COMPRESSOR_DECAY = 0.085  # 0.05
COMPRESSOR_THRES_DB = -15
COMPRESSOR_RATIO = 4

NOISE_GATE_DB = -999

BASS_FREQ_DB = 0
MIDDLE_FREQ_DB = -4
TREBLE_FREQ_DB = 1

PADDING = 0.15


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def _create_dir_if_not_exists(file):
    os.makedirs(os.path.dirname(file), exist_ok=True)


def create_normalized(name, in_file, mtime):
    out_file = f"tmp/{name}.final.wav"
    if (
        ALWAYS_GENERATE
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        subprocess.check_call(f"sox {in_file} {out_file} norm -7.5")
        os.utime(out_file, (mtime, mtime))
    return out_file


def process_audio_file(f):
    name_no_ext = os.path.splitext(os.path.basename(f))[0]
    mtime = os.path.getmtime(f)

    # Convert to mono
    in_file = f
    out_file = f"tmp/{f}.mono.wav"
    _create_dir_if_not_exists(out_file)
    if (
        ALWAYS_GENERATE
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        call2("sox %s %s channels 1" % (in_file, out_file))
        os.utime(out_file, (mtime, mtime))

    # Normalization
    in_file = out_file
    out_file = f"tmp/{f}.norm.wav"
    if (
        ALWAYS_GENERATE
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        # The loudnorm filter uses (overlapping) windows of 3 seconds of audio
        # to calculate short-term loudness in the source and adjust the destination
        # to meet the target parameters. The sample file is only a second long,
        # which looks to be the reason for the anomalous normalization.
        subprocess.check_call(
            f"ffmpeg -hide_banner -loglevel panic -i {in_file} -c:v copy -af apad=pad_len=80000,loudnorm=I={LOUDNESS_DB}:LRA=1 -ar 44100 {out_file} -y"
        )
        os.utime(out_file, (mtime, mtime))

    in_file = out_file
    filtered_voice_file = f"tmp/{f}.voice_only.wav"
    if (
        ALWAYS_GENERATE
        or not os.path.exists(filtered_voice_file)
        or os.path.getmtime(filtered_voice_file) != mtime
    ):
        print(filtered_voice_file)
        call2(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel",
                "panic",
                "-i",
                in_file,
                "-af",
                "lowpass=3000,highpass=200",
                filtered_voice_file,
                "-y",
            ]
        )
        os.utime(filtered_voice_file, (mtime, mtime))

    # Cut
    out_file = f"tmp/{f}.cut.wav"
    if (
        ALWAYS_GENERATE
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        rate, data2 = wavfile.read(in_file)
        border_samples = int(BORDER_IGNORE * rate)
        data2 = data2[border_samples:-border_samples]

        rate, data = wavfile.read(filtered_voice_file)
        data = data[border_samples:-border_samples]
        thres = np.max(np.abs(data)) * 0.1

        data0 = data
        keep = np.abs(data0) > thres

        keep_indices = np.argwhere(keep == True).flatten()
        start = max(keep_indices[0] - int(rate * PADDING), 0)
        end = min(keep_indices[-1] + int(rate * PADDING), data.shape[0])

        data2 = data2[start:end]

        zeros = np.zeros([int(rate * PADDING)], dtype=data2.dtype)
        data2 = np.concatenate((data2, zeros))

        # For visualization
        if False:
            indices = np.linspace(0, data.shape[0] - 1, 5000, dtype=int)
            data_vis = np.take(data, indices, axis=0)
            plt.plot(data_vis)
            plt.show()

        wavfile.write(out_file, rate, data2)
        os.utime(out_file, (mtime, mtime))

    # Compress
    in_file = out_file
    out_file = f"tmp/{f}.compressed.wav"
    _create_dir_if_not_exists(out_file)
    if (
        ALWAYS_GENERATE
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        subprocess.check_call(
            f"sox {in_file} {out_file}"
            f" equalizer 800 400h {MIDDLE_FREQ_DB}"
            f" bass {BASS_FREQ_DB} 100"
            f" treble {TREBLE_FREQ_DB} 4k 1s"
            f" compand"
            f" {COMPRESSOR_ATTACK},{COMPRESSOR_DECAY}"  # attack1,decay1
            f" {NOISE_GATE_DB-1},-inf"
            f",{NOISE_GATE_DB},{NOISE_GATE_DB}"
            f",{COMPRESSOR_THRES_DB},{COMPRESSOR_THRES_DB}"
            f",0,{COMPRESSOR_THRES_DB - COMPRESSOR_THRES_DB / COMPRESSOR_RATIO}"
            f" 0 -90"  # gain initial-volume-dB
        )
        os.utime(out_file, (mtime, mtime))

    out_file = create_normalized(name=f, in_file=out_file, mtime=mtime)

    return out_file


def create_final_vocal(prefix="record_", file_list=[]):
    # Filter out voice
    mkdir("tmp")
    mkdir("out")
    out_file_list = []

    if not file_list:
        file_list = sorted(glob.glob(prefix + "*.wav"))

    for f in file_list:
        out_file = process_audio_file(f)

        out_file_list.append(out_file)

    concat_audio(out_file_list, 0, out_file="out/concat.wav", channels=1)
    call2("start out/concat.wav")

    # subprocess.check_call(
    #     f'ffmpeg -hide_banner -loglevel panic -i out/concat.wav -c:v copy -af loudnorm=I={LOUDNESS_DB}:LRA=1 -ar 44100 out/concat.norm.wav -y')


if __name__ == "__main__":
    folder = r"{{_AUDIO_DIR}}"
    print("input audio folder: %s" % folder)
    chdir(folder)

    create_final_vocal()
