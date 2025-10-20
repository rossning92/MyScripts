import os
import subprocess

import numpy as np
from _shutil import call_echo

ALWAYS_GENERATE = False

# Cut voice
BORDER_IGNORE = 0.1
PADDING_SECS = 0.1
MIN_VOLUME_TO_KEEP = 0.05

# Loudness normalization
LOUDNORM_DB = -14

# Compressor
COMPRESSOR_ATTACK = 0.002
COMPRESSOR_DECAY = 0.085
COMPRESSOR_THRES_DB = -20
COMPRESSOR_RATIO = 4
COMPRESSOR_GAIN = 5

# EQ
EQ_PARAMS = "bass -0 30 equalizer 315 100h -1 equalizer 12105 10k 1"

NOISE_GATE_DB = -999


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def to_padded_mono(in_file, out_file, pad_secs=PADDING_SECS):
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    print(out_file)
    subprocess.check_call(
        [
            "sox",
            in_file,
            out_file,
            "channels",
            "1",
            "pad",
            "%g" % pad_secs,
            "%g" % pad_secs,
        ]
    )


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


def process_audio_file(file, out_file=None, cut_voice=True, compress=True, eq=False):
    from scipy.io import wavfile

    name_no_ext = os.path.splitext(os.path.basename(file))[0]

    if not out_file:
        out_file = os.path.join(os.path.dirname(file), "tmp", name_no_ext + ".wav")

    out_dir = os.path.dirname(out_file)

    # Convert to mono
    in_file = file
    out_file2 = out_dir + "/" + name_no_ext + ".mono.wav"
    to_padded_mono(in_file, out_file2)

    if LOUDNORM_DB != 0:
        # Loudnorm
        in_file = out_file2
        out_file2 = out_dir + "/" + name_no_ext + ".norm.wav"
        # loudnorm(in_file, out_file2, LOUDNORM_DB)
        normalize(in_file, out_file2, -1)
        in_file = out_file2

    if cut_voice:
        # Filter human voice
        filtered_voice_file = out_dir + "/" + name_no_ext + ".voice_only.wav"
        filter_human_voice(in_file, filtered_voice_file)

        # Cut only human voice part
        out_file2 = out_dir + "/" + name_no_ext + ".cut.wav"

        print(out_file2)
        rate, data2 = wavfile.read(in_file)
        border_samples = int(BORDER_IGNORE * rate)
        # data2 = data2[border_samples:-border_samples]

        rate, data = wavfile.read(filtered_voice_file)
        # data = data[border_samples:-border_samples]
        thres = np.max(np.abs(data)) * MIN_VOLUME_TO_KEEP

        data0 = data
        keep = np.abs(data0) > thres

        keep_indices = np.argwhere(keep == True).flatten()
        start = max(keep_indices[0] - int(rate * PADDING_SECS), 0)
        end = min(keep_indices[-1] + int(rate * PADDING_SECS), data.shape[0])

        data2 = data2[start:end]

        zeros = np.zeros([int(rate * PADDING_SECS)], dtype=data2.dtype)
        data2 = np.concatenate((data2, zeros))

        wavfile.write(out_file2, rate, data2)
        in_file = out_file2

    if compress:
        # out_file2 = out_dir + "/" + name_no_ext + ".compressed.wav"
        out_file2 = out_file
        os.makedirs(os.path.dirname(out_file2), exist_ok=True)

        print(out_file2)

        args = ["sox", in_file, out_file2]

        # Compressor
        args.extend(
            [
                "compand",
                f"{COMPRESSOR_ATTACK},{COMPRESSOR_DECAY}",  # attack1,decay1
                f"{NOISE_GATE_DB-1},-inf"
                f",{NOISE_GATE_DB},{NOISE_GATE_DB},{COMPRESSOR_THRES_DB},{COMPRESSOR_THRES_DB}"
                f",0,{COMPRESSOR_THRES_DB - COMPRESSOR_THRES_DB / COMPRESSOR_RATIO}",
                f"{COMPRESSOR_GAIN}",  # gain
                "-90",  # initial-volume-dB
            ]
        )

        if eq:
            args.extend(EQ_PARAMS.split())

        subprocess.check_call(args)

    # in_file = out_file2
    # out_file2 = out_dir + "/" + name_no_ext + ".norm.wav"
    # normalize(in_file, out_file2)

    return out_file2


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
