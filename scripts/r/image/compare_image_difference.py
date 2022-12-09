import numpy as np
from _image import show_im
from _shutil import get_files
from PIL import Image

files = get_files(cd=True)

a = np.array(Image.open(files[0]).convert("L"), dtype=float)
b = np.array(Image.open(files[1]).convert("L"), dtype=float)
diff = np.abs(a - b)
print("Sum of pixel difference: %.2f" % np.sum(diff))
show_im(diff)
