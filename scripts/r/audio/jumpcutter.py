from scipy.io import wavfile
from _shutil import *
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from _audio import *

BORDER_IGNORE = 0.1
LOUDNESS_DB = -14

COMPRESSOR_ATTACK = 0.0
COMPRESSOR_DECAY = 0.2  # 0.05
COMPRESSOR_THRES_DB = -20

NOISE_GATE_DB = -30

MIDDLE_FREQ_DB = -10
TREBLE_BOOST_DB = 2

PADDING = 0.2


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


def create_final_vocal():
    # Filter out voice
    mkdir('tmp/cut')
    mkdir('out')
    out_file_list = []
    out_norm_files = []
    for f in glob.glob('Audio*.wav'):
        print2('Processing: %s' % f)

        name_no_ext = os.path.splitext(os.path.basename(f))[0]

        # Convert to mono
        in_file = f
        out_file = 'tmp/%s.mono.wav' % name_no_ext
        if not os.path.exists(out_file):
            call2('sox %s %s channels 1' % (in_file, out_file))

        # Normalization
        in_file = out_file
        out_file = f'tmp/{f}.norm.wav'
        if not os.path.exists(out_file):
            # The loudnorm filter uses (overlapping) windows of 3 seconds of audio
            # to calculate short-term loudness in the source and adjust the destination
            # to meet the target parameters. The sample file is only a second long,
            # which looks to be the reason for the anomalous normalization.
            subprocess.check_call(
                f'ffmpeg -i {in_file} -c:v copy -af apad=pad_len=80000,loudnorm=I={LOUDNESS_DB}:LRA=1 -ar 44100 {out_file} -y')

        in_file = out_file
        filtered_voice_file = 'tmp/%s.voice_only.wav' % name_no_ext
        if not os.path.exists(filtered_voice_file):
            call2([
                'ffmpeg', '-i', in_file,
                '-af', 'lowpass=3000,highpass=200',
                filtered_voice_file,
                '-y'
            ])

        # Cut
        out_file = 'tmp/%s.cut.wav' % name_no_ext
        if not os.path.exists(out_file):
            rate, data2 = wavfile.read(in_file)
            border_samples = int(BORDER_IGNORE * rate)
            data2 = data2[border_samples:-border_samples]

            rate, data = wavfile.read(filtered_voice_file)
            data = data[border_samples:-border_samples]
            thres = np.max(np.abs(data)) * 0.1

            data0 = data
            keep = np.abs(data0) > thres

            # if False:
            #     data_roll_window = rolling_window(np.squeeze(data[:, 0]), 3)
            #     keep2 = np.abs(data_roll_window).any(axis=-1) > thres
            #     print(keep2)

            # if True:
            #     keep = rolling_window(keep, int(rate * 0.5))
            #     keep = keep.any(axis=-1)

            keep_indices = np.argwhere(keep == True).flatten()
            start = max(keep_indices[0] - int(rate * PADDING), 0)
            end = min(keep_indices[-1] + int(rate * PADDING), data.shape[0])

            data2 = data2[start:end]

            # For visualization
            if False:
                indices = np.linspace(0, data.shape[0] - 1, 5000, dtype=int)
                data_vis = np.take(data, indices, axis=0)
                plt.plot(data_vis)
                plt.show()

            wavfile.write(out_file, rate, data2)
        out_norm_files.append(out_file)

        # Compress
        in_file = out_file
        out_file = f'out/{f}'
        if not os.path.exists(out_file):
            subprocess.check_call(
                f'sox {in_file} {out_file}'
                f' equalizer 800 400h {MIDDLE_FREQ_DB}'
                f' treble {TREBLE_BOOST_DB} 4k 1s'
                f' compand'
                f' {COMPRESSOR_ATTACK},{COMPRESSOR_DECAY}'  # attack1,decay1
                f' {NOISE_GATE_DB-1},-90,{NOISE_GATE_DB},{NOISE_GATE_DB},{COMPRESSOR_THRES_DB},{LOUDNESS_DB},0,{LOUDNESS_DB}'
                f' 0 -90'  # gain initial-volume-dB

            )

        out_file_list.append(out_file)

    concat_audio(out_file_list, 0.2, out_file='out/concat.wav', channels=1)
    concat_audio(out_norm_files, 0.2, out_file='out/concat_norm.wav', channels=1)
    call2('start out/concat.wav')


if __name__ == '__main__':
    chdir(os.environ['CURRENT_FOLDER'])

    create_final_vocal()
