from _audio import *

chdir(os.environ['CUR_DIR_'])

for f in glob.glob('*.wav'):
    denoise(f)
