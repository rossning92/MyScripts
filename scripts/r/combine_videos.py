from _video import *
from _shutil import *

files = get_files(cd=True)
titles = [os.path.splitext(x)[0] for x in files]

generate_video_matrix(files, titles, 'combined.mp4')
