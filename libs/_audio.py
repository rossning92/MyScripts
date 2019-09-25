from _shutil import *


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
