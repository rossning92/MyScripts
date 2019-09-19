from _shutil import *

f = get_files(cd=True)[0]
name_no_ext = os.path.splitext(f)[0]
mkdir(name_no_ext)
args = f'ffmpeg -i "{f}" -vf fps={{_FPS}} -qscale:v 2 "{name_no_ext}/%03d.jpg"'
# set_clip(args)
call2(args)
