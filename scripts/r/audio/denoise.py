from _audio import *

chdir(os.environ["CWD"])

for f in glob.glob("*.wav"):
    denoise(f)
