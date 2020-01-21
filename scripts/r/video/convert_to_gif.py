import os
import sys
import subprocess
from _appmanager import *
from _shutil import *

get_executable('magick')


fps = '{{_FPS}}' if '{{_FPS}}' else 15

f = os.environ['SELECTED_FILE']
os.chdir(os.path.dirname(f))
file_name = os.path.basename(f)

# Convert video to gif
# fps=25,scale=w=-1:h=480
out_gif = os.path.splitext(file_name)[0] + '.gif'
args = f'ffmpeg -i "{file_name}" -filter_complex "[0:v] fps={fps},split [a][b];[a] palettegen=stats_mode=single [p];[b][p] paletteuse=new=1" "{out_gif}" -y'
call2(args)

# Optimize gif
print2('Optimize gif...')
out_gif_optimized = os.path.splitext(f)[0] + '_optimized.gif'
args = f'magick "{out_gif}" -coalesce -fuzz 4%% +dither -layers Optimize "{out_gif_optimized}"'
call2(args)