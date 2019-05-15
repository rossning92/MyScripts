from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

combine_images(image_files='*.png',
               out_file='out.png',
               cols={{COMBINE_IMG_COLS}})
