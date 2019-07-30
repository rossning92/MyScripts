from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

cols = '{{COMBINE_IMG_COLS}}'
cols = int(cols) if cols else None
col_major_order = True if '{{COMBINE_IMG_COL_MAJOR_ORDER}}' else False
draw_label = True if '{{COMBINE_IMG_DRAW_LABEL}}' else False
label_align = '{{COMBINE_IMG_LABEL_ALIGN}}' if '{{COMBINE_IMG_LABEL_ALIGN}}' else 'center'
gif_duration = int('{{COMBINE_IMG_GIF_DURA}}') if '{{COMBINE_IMG_GIF_DURA}}' else 500
font_scale = float('{{COMBINE_IMG_FONT_SCALE}}') if '{{COMBINE_IMG_FONT_SCALE}}' else 1.0

combine_images(image_files='*.png',
               out_file='out/out.png',
               cols=cols,
               col_major_order=col_major_order,
               draw_label=draw_label,
               label_align=label_align,
               gif_duration=gif_duration,
               font_scale=font_scale)
