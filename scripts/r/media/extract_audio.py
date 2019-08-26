from _shutil import *

in_file = get_files(cd=True)[0]
call2(["ffmpeg", "-i", in_file, "-vn", "-acodec", "mp3", "output_audio.mp3"])
