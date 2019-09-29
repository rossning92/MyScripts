from _shutil import *

in_file = get_files(cd=True)[0]
out_file = 'out' + os.path.splitext(in_file)[1]
start, duration = '{{_START_AND_DURATION}}'.split()

call2(f'ffmpeg -i "{in_file}" -ss {start} -strict -2 -t {duration} "{out_file}.mp4"')