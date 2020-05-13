from _video import *
from _shutil import *

files = sorted(get_files(cd=True))
titles = [os.path.splitext(x)[0] for x in files]


crop_rect = [int(x) for x in '{{COMBINE_VID_CROP_RECT}}'.split()] if '{{COMBINE_VID_CROP_RECT}}' else None

generate_video_matrix(files, titles, 'combined.mp4', crop_rect=crop_rect)
