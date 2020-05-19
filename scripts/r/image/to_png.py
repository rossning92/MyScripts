from PIL import Image
from _shutil import *


for f in get_files():
    if not f.endswith('.png'):
        with Image.open(f) as im:
            im.save(os.path.splitext(f)[0] + '.png')
