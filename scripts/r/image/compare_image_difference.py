import argparse

import numpy as np
from _image import show_im
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument("files", nargs=2)
args = parser.parse_args()

a = np.array(Image.open(args.files[0]), dtype=float)
b = np.array(Image.open(args.files[1]), dtype=float)
diff = np.abs(a - b)
print("sum of pixel diff: %.2f" % np.sum(diff))
print("avg of pixel diff: %.2f" % np.mean(diff))
show_im(diff, split_channels=True)
