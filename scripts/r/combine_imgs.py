from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

cols = '{{COMBINE_IMG_COLS}}'
cols = int(cols) if cols else None
col_major_order = True if '{{COMBINE_IMG_COL_MAJOR_ORDER}}' else False

combine_images(image_files='*.png',
               out_file='out/out.png',
               cols=cols,
               col_major_order=col_major_order)
