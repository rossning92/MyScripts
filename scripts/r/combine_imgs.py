from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

cols = '{{COMBINE_IMG_COLS}}'
cols = int(cols) if cols else None
col_major_order = True if '{{COMBINE_IMG_COL_MAJOR_ORDER}}' else False
draw_label = bool('{{COMBINE_IMG_DRAW_LABEL}}')
label_align = '{{COMBINE_IMG_LABEL_ALIGN}}' if '{{COMBINE_IMG_LABEL_ALIGN}}' else 'center'

combine_images(image_files='*.png',
               out_file='out/out.png',
               cols=cols,
               col_major_order=col_major_order,
               draw_label=draw_label,
               label_align=label_align)
