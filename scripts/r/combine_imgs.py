from _image import *
from _shutil import *

os.chdir(env['CURRENT_FOLDER'])

cols = '{{_COLS}}'
cols = int(cols) if cols else None
col_major_order = True if '{{_COL_MAJOR_ORDER}}' else False
draw_label = True if '{{_DRAW_LABEL}}' else False
label_align = '{{_LABEL_ALIGN}}' if '{{_LABEL_ALIGN}}' else 'center'
gif_duration = int('{{_GIF_DURA}}') if '{{_GIF_DURA}}' else 500
font_scale = float('{{_FONT_SCALE}}') if '{{_FONT_SCALE}}' else 1.0
font_color = '{{_FONT_COLOR}}' if '{{_FONT_COLOR}}' else 'white'

combine_images(image_files='*.png',
               out_file='out/out.png',
               cols=cols,
               col_major_order=col_major_order,
               draw_label=draw_label,
               label_align=label_align,
               gif_duration=gif_duration,
               font_scale=font_scale,
               font_color=font_color)
