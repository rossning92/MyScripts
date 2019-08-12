from _shutil import *
from _image import *

files = get_files(cd=True)

mkdir('cropped')

rect = [float(x) for x in '{{CROP_IMG_RECT}}'.split()]

for f in files:
    copy(f, 'cropped/' + f)
    crop_image_file('cropped/' + f, rect_normalized=rect)
