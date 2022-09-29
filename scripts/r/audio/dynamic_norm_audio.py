from postprocess import dynamic_audio_normalize
from _shutil import *

f = get_files()[0]
dynamic_audio_normalize(f)
