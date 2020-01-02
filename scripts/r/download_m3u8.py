from _shutil import *

url = get_clip()
# if not url.endswith('.m3u8'):
#     sys.exit(1)

chdir(expanduser('~/Desktop'))

call2('ffmpeg -i %s -c copy -bsf:a aac_adtstoasc %s.mp4' % (url, get_cur_time_str()))
