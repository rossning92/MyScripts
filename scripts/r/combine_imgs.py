import argparse
import os

from _image import combine_images
from utils.shutil import shell_open

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("image_files", nargs="+")
    parser.add_argument("-o", "--out-file", default="out/out.png")
    args = parser.parse_args()

    cols = int("{{_NUM_COLS}}") if "{{_NUM_COLS}}" else None
    col_major_order = True if "{{_COL_MAJOR_ORDER}}" else False
    draw_label = True if "{{_DRAW_LABEL}}" else False
    label_align = "{{_LABEL_ALIGN}}" if "{{_LABEL_ALIGN}}" else "bottom"
    gif_duration = int("{{_GIF_DURA}}") if "{{_GIF_DURA}}" else 500
    font_scale = float("{{_FONT_SCALE}}") if "{{_FONT_SCALE}}" else 1.0
    font_color = "{{_FONT_COLOR}}" if "{{_FONT_COLOR}}" else "white"
    spacing = int("{{_SPACING}}") if "{{_SPACING}}" else 4

    combine_images(
        image_files=args.image_files,
        out_file=args.out_file,
        cols=cols,
        col_major_order=col_major_order,
        draw_label=draw_label,
        label_align=label_align,
        generate_gif=True if "{{_GEN_GIF}}" else False,
        generate_vid=True if "{{_GEN_VID}}" else False,
        generate_atlas=True if "{{_GEN_ATLAS}}" else False,
        gif_duration=gif_duration,
        font_scale=font_scale,
        font_color=font_color,
        spacing=spacing,
    )

    out_gif = os.path.splitext(args.out_file)[0] + ".gif"
    shell_open(os.path.abspath(out_gif if "{{_GEN_GIF}}" else args.out_file))
