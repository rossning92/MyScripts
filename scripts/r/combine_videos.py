from _video import *
import os
import glob

os.chdir(os.environ['CURRENT_FOLDER'])
files = list(glob.glob('*.mp4')) + list(glob.glob('*.avi'))
titles = [os.path.splitext(x)[0] for x in files]
print(files)

generate_video_matrix(files, titles, 'combined.mp4')
