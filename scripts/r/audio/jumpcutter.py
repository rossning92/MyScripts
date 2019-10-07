from scipy.io import wavfile
from _shutil import *
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from _audio import *


def rolling_window(a, window):
    shape = a.shape[:-1] + (a.shape[-1] - window + 1, window)
    strides = a.strides + (a.strides[-1],)
    return np.lib.stride_tricks.as_strided(a, shape=shape, strides=strides)


chdir(os.environ['CURRENT_FOLDER'])

# Filter out voice
mkdir('tmp/filtered_voice')
for f in glob.glob('*.wav'):
    call2([
        'ffmpeg', '-i', f,
        '-af', 'lowpass=3000,highpass=200',
        'tmp/filtered_voice/%s' % f,
        '-y'
    ])

mkdir('tmp/cut')
for f in glob.glob('tmp/filtered_voice/*'):
    filtered_voice_file = f
    original_file = os.path.basename(f)

    rate, data2 = wavfile.read(original_file)

    rate, data = wavfile.read(filtered_voice_file)
    thres = np.max(np.abs(data)) * 0.1

    data0 = data[:, 0]
    keep = np.abs(data0) > thres

    # if False:
    #     data_roll_window = rolling_window(np.squeeze(data[:, 0]), 3)
    #     keep2 = np.abs(data_roll_window).any(axis=-1) > thres
    #     print(keep2)

    # if True:
    #     keep = rolling_window(keep, int(rate * 0.5))
    #     keep = keep.any(axis=-1)

    keep_indices = np.argwhere(keep == True).flatten()
    start = max(keep_indices[0] - int(rate * 0.25), 0)
    end = min(keep_indices[-1] + int(rate * 0.25), data.shape[0])

    data2 = data2[start:end, :]

    # For visualization
    if False:
        indices = np.linspace(0, data.shape[0] - 1, 5000, dtype=int)
        data_vis = np.take(data, indices, axis=0)
        plt.plot(data_vis)
        plt.show()

    wavfile.write('tmp/cut/%s' % original_file, rate, data2)

# Post process
mkdir('out')
for f in glob.glob('*.wav'):
    print2(f)
    base_name = os.path.basename(f)
    # subprocess.call([
    #     'ffmpeg', '-i', f,
    #     '-filter_complex', 'loudnorm,'
    #                        'acompressor=threshold=-21dB:ratio=4:attack=10:release=250,'
    #                        'equalizer=f=1:width_type=h:width=40:g=-20,'
    #                        'equalizer=f=80:width_type=h:width=40:g=5,'
    #                        'equalizer=f=700:width_type=h:width=400:g=-10,'
    #                        'equalizer=f=12500:width_type=h:width=999:g=10,'
    #                        'loudnorm',
    #
    #     # '-af', 'equalizer=f=1000:t=h:width=200:g=-50',
    #     'out/%s' % base_name,
    #     '-y'
    # ])

    subprocess.check_call(f'ffmpeg -i tmp/cut/{f} -c:v copy -af loudnorm=I=-14:LRA=1 -ar 44100 tmp/{f}.norm.wav -y')
    # subprocess.call(f'sox --norm=-3 tmp/cut/{f} tmp/{f}.norm.wav')
    # subprocess.call(f'sox tmp/cut/{f} tmp/{f}.norm.wav loudness -14')

    THRES = '-10'
    subprocess.check_call(f'sox tmp/{f}.norm.wav out/{f}'
                          f' compand'
                          f' 0.005,0.2'  # attack1,decay1
                          f' -31,-90,-30,-30,{THRES},{THRES},0,{THRES}'
                          f' 0 -90'  # gain initial-volume-dB
                          f' equalizer 800 400h -10 treble 5 4k 1s')
