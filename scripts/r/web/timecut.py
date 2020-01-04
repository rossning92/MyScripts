from _shutil import *

setup_nodejs()

f = get_files(cd=True)[0]

call2(f'timecut {f} --viewport=1920,1080 --fps=25 --duration=1 --frame-cache --pix-fmt=yuv420p --output=video.mp4')
