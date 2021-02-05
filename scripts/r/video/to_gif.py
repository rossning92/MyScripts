import os
import sys
import subprocess
from _appmanager import *
from _shutil import *


fps = "{{_FPS}}" if "{{_FPS}}" else 15

cur_folder = get_current_folder()
mkdir(os.path.join(cur_folder, "out"))
cd(cur_folder)

for f in get_files(cd=True):
    file_name = os.path.basename(f)

    # Convert video to gif
    # fps=25,scale=w=-1:h=480
    out_gif = os.path.join("out", os.path.splitext(file_name)[0] + ".gif")
    args = [f"ffmpeg", "-i", file_name, "-filter_complex"]

    # Filter complex
    filter = f"[0:v] fps={fps}"
    if "{{_SCALE_H}}":
        filter += ",scale=-1:{{_SCALE_H}}"
    filter += ",split [a][b];"

    if "{{_SINGLE_PALETTE}}":
        filter += "[a] palettegen [p];[b][p] paletteuse"
    else:
        filter += "[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1"

    args.append(filter)

    args += [out_gif, "-y"]

    call_echo(args)

    # Optimize gif
    if "{{_OPTIMIZE_GIF}}":
        print2("Optimize gif...")
        out_gif_optimized = os.path.join(
            "out", os.path.splitext(f)[0] + ".optimized.gif"
        )
        args = f'magick "{out_gif}" -coalesce -fuzz 4%% +dither -layers Optimize "{out_gif_optimized}"'
        call2(args)
