import matplotlib.pyplot as plt
import numpy as np
from _shutil import *
from _image import *
from _math import *

if "{{_DTYPE}}" == "f32":
    dtype = np.float32
elif "{{_DTYPE}}" == "f16":
    dtype = np.float16
else:
    dtype = np.uint8

f = get_files()[0]

im = np.fromfile(f, dtype=dtype)
if dtype == np.float16:
    im = im.astype(np.float32)

width, height = [int(x) for x in "{{_SIZE}}".split()]

shape = [height, width]
if "{{_CHANNEL}}":
    shape.append({{_CHANNEL}})

im = im.reshape(shape)
print(im)

show_im(im, split_channels=bool("{{_SPLIT_CHANNELS}}"))
