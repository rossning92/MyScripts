from _shutil import *
from _appmanager import *

get_executable('sox')


def create_noise_profile(in_file):
    call2(['sox', in_file, '-n', 'noiseprof', 'noise.prof'])


def denoise(in_file, out_file=None):
    if os.path.exists('noise.prof'):
        if out_file is None:
            out_file_tmp = in_file + 'denoise.wav'
        else:
            out_file_tmp = out_file

        print('De-noising %s...' % in_file)
        call2(['sox', in_file, out_file_tmp, 'noisered', 'noise.prof', '0.21'])

        if out_file is None:
            copy(out_file_tmp, in_file)
            os.remove(out_file_tmp)

    else:
        print('WARNING: Skip noise reduction: profile does not exist.')


def concat_audio(audio_files, silence_secs, out_file, channels=2):
    call2(f'sox -n -r 44100 -c {channels} tmp/silence.wav trim 0.0 {silence_secs}')

    mkdir('tmp')
    audio_files = ' tmp/silence.wav '.join(audio_files)

    print2('Output %s' % out_file)
    call2(f'sox {audio_files} {out_file}')
