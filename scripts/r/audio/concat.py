from _audio import *

if __name__ == '__main__':
    silence_secs = float('{{_SILENCE_SECS}}') if '{{_SILENCE_SECS}}' else 1.0
    chdir(os.environ['CUR_DIR_'])
    audio_files = list(glob.glob('*.wav'))

    mkdir('out')
    concat_audio(audio_files, silence_secs, out_file='out/concat.wav')
