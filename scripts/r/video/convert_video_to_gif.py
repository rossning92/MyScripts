import os
import sys
import subprocess

f = os.environ['SELECTED_FILE']
os.chdir(os.path.dirname(f))
file_name = os.path.basename(f)

# Convert video to gif
# fps=25,scale=w=-1:h=480
out_gif = os.path.splitext(file_name)[0] + '.gif'
args = f'ffmpeg -i "{file_name}" -filter_complex "[0:v] fps=15,split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" {out_gif}'
subprocess.call(args)

# Optimize gif
out_gif_optimized = os.path.splitext(f)[0] + '_optimized.gif'
args = f'magick {out_gif} -coalesce -fuzz 4%% +dither -layers Optimize {out_gif_optimized}'
