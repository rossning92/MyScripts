from _audio import *
from _cache import *
from _shutil import *
from scipy.io import wavfile
import matplotlib.pyplot as plt
import numpy as np

ALWAYS_GENERATE = False

BORDER_IGNORE = 0.1
LOUDNORM_DB = -14


COMPRESSOR_ATTACK = 0.002
COMPRESSOR_DECAY = 0.085
COMPRESSOR_THRES_DB = -20
COMPRESSOR_RATIO = 4
COMPRESSOR_GAIN = 5

EQ_PARAMS = "bass -0 30 equalizer 315 100h -1 equalizer 12105 10k 1"
EQ_PARAMS = ""

NORMALIZE_DB = -7.5

NOISE_GATE_DB = -999

RECORD_MIN_VOLUME_TO_KEEP = 0.05

PADDING = 0.15


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def _create_dir_if_not_exists(file):
    os.makedirs(os.path.dirname(file), exist_ok=True)


def to_mono(in_file, out_file):
    _create_dir_if_not_exists(out_file)
    print(out_file)
    subprocess.check_call(["sox", in_file, out_file, "channels", "1"])


def loudnorm(in_file, out_file, loudnorm_db=LOUDNORM_DB):
    # The loudnorm filter uses (overlapping) windows of 3 seconds of audio
    # to calculate short-term loudness in the source and adjust the destination
    # to meet the target parameters. The sample file is only a second long,
    # which looks to be the reason for the anomalous normalization.
    subprocess.check_call(
        f'ffmpeg -hide_banner -loglevel panic -i "{in_file}" -c:v copy -af apad=pad_len=80000,loudnorm=I={loudnorm_db}:LRA=1 -ar 44100 "{out_file}" -y'
    )


def normalize(in_file, out_file, normalize_db):
    subprocess.check_call(["sox", in_file, out_file, "norm", "%g" % normalize_db])


def filter_human_voice(in_file, out_file):
    print(out_file)
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
            out_file,
            "-y",
        ]
    )


def _process_audio_file(file, out_dir):
    name_no_ext = os.path.splitext(os.path.basename(file))[0]

    # Convert to mono
    in_file = file
    out_file = out_dir + "/" + name_no_ext + ".mono.wav"
    to_mono(in_file, out_file)

    if LOUDNORM_DB != 0:
        # Loudnorm
        in_file = out_file
        out_file = out_dir + "/" + name_no_ext + ".norm.wav"
        loudnorm(in_file, out_file, LOUDNORM_DB)

    # Filter human voice
    in_file = out_file
    filtered_voice_file = out_dir + "/" + name_no_ext + ".voice_only.wav"
    filter_human_voice(in_file, filtered_voice_file)

    # Cut only human voice part
    out_file = out_dir + "/" + name_no_ext + ".cut.wav"

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

    # Compress
    if 1:
        in_file = out_file
        out_file = out_dir + "/" + name_no_ext + ".compressed.wav"
        _create_dir_if_not_exists(out_file)

        print(out_file)

        args = f'sox "{in_file}" "{out_file}"'

        # Compressor
        args += (
            f" compand"
            f" {COMPRESSOR_ATTACK},{COMPRESSOR_DECAY}"  # attack1,decay1
            f" {NOISE_GATE_DB-1},-inf"
            f",{NOISE_GATE_DB},{NOISE_GATE_DB}"
            f",{COMPRESSOR_THRES_DB},{COMPRESSOR_THRES_DB}"
            f",0,{COMPRESSOR_THRES_DB - COMPRESSOR_THRES_DB / COMPRESSOR_RATIO}"
            f" {COMPRESSOR_GAIN} -90"  # gain initial-volume-dB
        )

        # EQ
        args += " " + EQ_PARAMS

        subprocess.check_call(args)

    # in_file = out_file
    # out_file = out_dir + "/" + name_no_ext + ".norm.wav"
    # normalize(in_file, out_file)

    return out_file


def dynamic_audio_normalize(file):
    tmp_dir = os.path.join(os.path.dirname(file), "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    out_file = os.path.join(tmp_dir, os.path.basename(file))
    if not os.path.exists(out_file):
        call_echo(
            [
                "ffmpeg",
                "-i",
                file,
                "-af",
                "dynaudnorm=p=1/sqrt(2):m=100:s=12:g=15",
                out_file,
            ]
        )
    return out_file


def process_audio_file(file, out_dir="tmp"):
    @file_cache
    def process_audio_file(file, out_dir, mtime):
        return _process_audio_file(file, out_dir)

    return process_audio_file(file, out_dir, os.path.getmtime(file))


if __name__ == "__main__":
    # folder = r"{{_AUDIO_DIR}}"
    # print("input audio folder: %s" % folder)
    # chdir(folder)

    f = get_files(cd=True)[0]
    out = process_audio_file(f)
    subprocess.call(["ffplay", "-nodisp", out])

