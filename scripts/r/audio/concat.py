from _audio import *

silence_secs = float('{{_SILENCE_SECS}}') if '{{_SILENCE_SECS}}' else 1.0

chdir(os.environ['CURRENT_FOLDER'])

mkdir('tmp')
mkdir('out')
call2(f'sox -n -r 44100 -c 2 tmp/silence.wav trim 0.0 {silence_secs}')

audios = list(glob.glob('*.wav'))
audios = ' tmp/silence.wav '.join(audios)

print2('Output out/concat.wav')
call2(f'sox {audios} out/concat.wav')
