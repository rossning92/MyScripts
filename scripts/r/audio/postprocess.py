from scipy.io import wavfile
from _shutil import *
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from _audio import *

ALWAYS_GENERATE = False

BORDER_IGNORE = 0.1
LOUDNESS_DB = -14

COMPRESSOR_ATTACK = 0.002
COMPRESSOR_DECAY = 0.085
COMPRESSOR_THRES_DB = -15
COMPRESSOR_RATIO = 4

NOISE_GATE_DB = -999

RECORD_MIN_VOLUME_TO_KEEP = 0.05

PADDING = 0.15


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def _create_dir_if_not_exists(file):
    os.makedirs(os.path.dirname(file), exist_ok=True)


def create_normalized(*, out_file, in_file, mtime, regenerate):
    if (
        regenerate
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        subprocess.check_call(["sox", in_file, out_file, "norm", "-7.5"])
        os.utime(out_file, (mtime, mtime))


def process_audio_file(f, regenerate=ALWAYS_GENERATE, out_dir="tmp"):
    name_no_ext = os.path.splitext(os.path.basename(f))[0]
    mtime = os.path.getmtime(f)

    # Convert to mono
    in_file = f
    out_file = out_dir + "/" + name_no_ext + ".mono.wav"
    _create_dir_if_not_exists(out_file)
    if (
        regenerate
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        subprocess.check_call(["sox", in_file, out_file, "channels", "1"])
        os.utime(out_file, (mtime, mtime))

    # Normalization
    in_file = out_file
    out_file = out_dir + "/" + name_no_ext + ".norm.wav"
    if (
        regenerate
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        # The loudnorm filter uses (overlapping) windows of 3 seconds of audio
        # to calculate short-term loudness in the source and adjust the destination
        # to meet the target parameters. The sample file is only a second long,
        # which looks to be the reason for the anomalous normalization.
        subprocess.check_call(
            f'ffmpeg -hide_banner -loglevel panic -i "{in_file}" -c:v copy -af apad=pad_len=80000,loudnorm=I={LOUDNESS_DB}:LRA=1 -ar 44100 "{out_file}" -y'
        )
        os.utime(out_file, (mtime, mtime))

    in_file = out_file
    filtered_voice_file = out_dir + "/" + name_no_ext + ".voice_only.wav"
    if (
        regenerate
        or not os.path.exists(filtered_voice_file)
        or os.path.getmtime(filtered_voice_file) != mtime
    ):
        print(filtered_voice_file)
        subprocess.check_call(
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
    out_file = out_dir + "/" + name_no_ext + ".cut.wav"
    if (
        regenerate
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)
        rate, data2 = wavfile.read(in_file)
        border_samples = int(BORDER_IGNORE * rate)
        data2 = data2[border_samples:-border_samples]

        rate, data = wavfile.read(filtered_voice_file)
        data = data[border_samples:-border_samples]
        thres = np.max(np.abs(data)) * RECORD_MIN_VOLUME_TO_KEEP

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
    out_file = out_dir + "/" + name_no_ext + ".compressed.wav"
    _create_dir_if_not_exists(out_file)
    if (
        regenerate
        or not os.path.exists(out_file)
        or os.path.getmtime(out_file) != mtime
    ):
        print(out_file)

        args = f'sox "{in_file}" "{out_file}"'

        # EQ
        if 0:  # old
            args += " bass -2.0 100" " equalizer 800 400h -4.0" " treble 1.0 4k 1s"
        else:
            args += " bass -10 30" " equalizer 315 100h -1" " equalizer 12105 10k 3"

        # Compressor
        args += (
            f" compand"
            f" {COMPRESSOR_ATTACK},{COMPRESSOR_DECAY}"  # attack1,decay1
            f" {NOISE_GATE_DB-1},-inf"
            f",{NOISE_GATE_DB},{NOISE_GATE_DB}"
            f",{COMPRESSOR_THRES_DB},{COMPRESSOR_THRES_DB}"
            f",0,{COMPRESSOR_THRES_DB - COMPRESSOR_THRES_DB / COMPRESSOR_RATIO}"
            f" 0 -90"  # gain initial-volume-dB
        )

        subprocess.check_call(args)
        os.utime(out_file, (mtime, mtime))

    # Normalize
    in_file = out_file
    out_file = out_dir + "/" + name_no_ext + ".final.wav"
    create_normalized(
        out_file=out_file, in_file=in_file, mtime=mtime, regenerate=regenerate
    )

    return out_file


def dynamic_audio_normalize(f):
    name, ext = os.path.splitext(f)
    out_file = "%s-norm%s" % (name, ext)
    if not os.path.exists(out_file):
        call_echo(
            [
                "ffmpeg",
                "-i",
                f,
                "-af",
                "dynaudnorm=p=1/sqrt(2):m=100:s=12:g=15",
                out_file,
            ]
        )
    return out_file


if __name__ == "__main__":
    # folder = r"{{_AUDIO_DIR}}"
    # print("input audio folder: %s" % folder)
    # chdir(folder)

    f = get_files(cd=True)[0]
    out = process_audio_file(f, regenerate=True)
    subprocess.call(["ffplay", "-nodisp", out])

