from _image import *
from _shutil import *


cols = int("{{_COLS}}") if "{{_COLS}}" else None
col_major_order = True if "{{_COL_MAJOR_ORDER}}" else False
draw_label = True if "{{_DRAW_LABEL}}" else False
label_align = "{{_LABEL_ALIGN}}" if "{{_LABEL_ALIGN}}" else "bottom"
gif_gen = True if "{{_GIF_GENERATION}}" else False
gif_duration = int("{{_GIF_DURA}}") if "{{_GIF_DURA}}" else 500
font_scale = float("{{_FONT_SCALE}}") if "{{_FONT_SCALE}}" else 1.0
font_color = "{{_FONT_COLOR}}" if "{{_FONT_COLOR}}" else "white"

combine_images(
    image_files=sorted(get_files(cd=True)),
    out_file="out/out.png",
    cols=cols,
    col_major_order=col_major_order,
    draw_label=draw_label,
    label_align=label_align,
    generate_gif=gif_gen,
    gif_duration=gif_duration,
    font_scale=font_scale,
    font_color=font_color,
)

call2("start out/out.png")
