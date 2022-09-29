from PIL import Image
from _shutil import *


for f in get_files():
    if not f.endswith(".png"):
        im = Image.open(f).convert("RGBA")
        im.save(os.path.splitext(f)[0] + ".png")
