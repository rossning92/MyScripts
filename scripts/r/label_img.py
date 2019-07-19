from _image import *
from _shutil import *
from _gui import *
from PIL import Image

f = get_files(cd=True)[0]

call(['notepad.exe', 'string.txt'])

with open('string.txt', 'r') as fp:
    text = fp.read()

im = Image.open(f)
draw_text(im, text, (0, 0, im.width, im.height), align='center')
fn, ext = os.path.splitext(f)
im.save(fn + '_labelled' + ext)
