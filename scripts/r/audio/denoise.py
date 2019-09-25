from _audio import *

chdir(os.environ['CURRENT_FOLDER'])

for f in glob.glob('*.wav'):
    denoise(f)
