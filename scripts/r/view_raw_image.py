import matplotlib.pyplot as plt
import numpy as np
from _shutil import *
from _image import *

f = get_files()[0]
im = np.fromfile(f, dtype=np.uint8)

width, height = [int(x) for x in "{{_SIZE}}".split()]

shape = [height, width]
if "{{_CHANNEL}}":
    shape.append({{_CHANNEL}})

im = im.reshape(shape)
print(im)

show_im(im, split_channels=bool("{{_SPLIT_CHANNELS}}"))
