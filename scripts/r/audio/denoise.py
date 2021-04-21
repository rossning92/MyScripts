from _audio import *

chdir(os.environ['_CUR_DIR'])

for f in glob.glob('*.wav'):
    denoise(f)
