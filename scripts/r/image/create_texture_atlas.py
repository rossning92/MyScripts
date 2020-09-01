from _shutil import *
from _image import *
import numpy as np


cd(os.environ['_CUR_DIR'])
mkdir('out')

atlas = None
files = sorted(os.listdir('.'))
files = [x for x in files if x.endswith(
    '.jpg') or x.endswith('.png') or x.endswith('.bmp')]

cols = rows = int(math.ceil(math.sqrt(len(files))))


for i, f in enumerate(files):
    im = Image.open(f)

    if atlas is None:
        atlas = Image.new('RGB', size=(cols * im.width, rows * im.height))

    atlas.paste(im, box=(i % cols * im.width, (rows - i // rows) * im.height))

print(cols, rows, len(files))
atlas.save('out/atlas.png')
