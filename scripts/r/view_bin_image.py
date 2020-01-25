import matplotlib.pyplot as plt
import numpy as np
from _shutil import *
from _image import *

f = get_files()[0]
im = np.fromfile(f, dtype=np.uint8)

shape = [{{_H}}, {{_W}}]
if '{{_CHANNEL}}':
    shape.append({{_CHANNEL}})
im = im.reshape(shape)
print(im)

show_im(im)