from _shutil import *

FPS = 25
DURATION = int('{{_DURA}}') if '{{_DURA}}' else 1

setup_nodejs()
input_file = get_files(cd=True)[0]

# https://github.com/tungs/timesnap

# call2(f'timecut {f} --pipe-mode'
#       f' --viewport=1920,1080'
#       f' --fps=25 --duration=1'
#       f' --frame-cache'
#       f' --pix-fmt=yuv420p'
#       f' --output=video.mp4')


call2(f'timesnap {input_file}'
      f' --viewport=1920,1080'
      f' --fps={FPS}'
      f' --duration={DURATION}'
      f' --output-stdout'
      f' | ffmpeg -framerate {FPS} -i pipe:0 -y video.mp4')
