import argparse
import os
from typing import Any

import numpy as np
from _image import show_im

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str, help="file path")
    args = parser.parse_args()

    dtype: Any
    requested_dtype = os.environ.get("_DTYPE", "")
    if requested_dtype == "f32":
        dtype = np.float32
    elif requested_dtype == "f16":
        dtype = np.float16
    elif requested_dtype == "i16":
        dtype = np.int16
    else:
        dtype = np.uint8

    im = np.fromfile(args.file, dtype=dtype)
    if dtype == np.float16:
        im = im.astype(np.float32)

    width = int(os.environ["_WIDTH"])
    height = int(os.environ["_HEIGHT"])

    shape = [height, width]
    if os.environ.get("_CHANNEL"):
        shape.append(int(os.environ["_CHANNEL"]))

    im = im.reshape(shape)
    print(im)

    show_im(im, split_channels=bool(os.environ.get("_SPLIT_CHANNELS")))
