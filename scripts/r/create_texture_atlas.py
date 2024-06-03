import glob
import os

from _image import combine_images
from _shutil import cd, get_current_folder
from utils.shutil import shell_open

if __name__ == "__main__":
    cols = int("{{_COLS}}") if "{{_COLS}}" else None
    col_major_order = True if "{{_COL_MAJOR_ORDER}}" else False
    draw_label = True if "{{_DRAW_LABEL}}" else False
    label_align = "{{_LABEL_ALIGN}}" if "{{_LABEL_ALIGN}}" else "bottom"
    font_scale = float("{{_FONT_SCALE}}") if "{{_FONT_SCALE}}" else 1.0
    font_color = "{{_FONT_COLOR}}" if "{{_FONT_COLOR}}" else "white"
    spacing = int("{{_SPACING}}") if "{{_SPACING}}" else 4

    cd(get_current_folder())
    files = sorted(glob.glob(os.path.join("**", "*.png")))

    combine_images(
        image_files=files,
        out_file="out/out.png",
        cols=cols,
        col_major_order=col_major_order,
        draw_label=draw_label,
        label_align=label_align,
        generate_atlas=True,
        font_scale=font_scale,
        font_color=font_color,
        spacing=spacing,
    )

    shell_open("out/out.png")
