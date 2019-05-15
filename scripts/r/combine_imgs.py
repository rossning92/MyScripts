from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

cols = '{{COMBINE_IMG_COLS}}'
cols = int(cols) if cols else None

combine_images(image_files='*.png',
               out_file='out.png',
               cols=cols)
