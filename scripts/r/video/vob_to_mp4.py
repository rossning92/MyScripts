from _video import *
from _shutil import *

vob_files = [x for x in sorted(get_files(cd=True))
             if x.lower().endswith('.vob')]
ffmpeg(in_file='concat:' + '|'.join(vob_files),
       reencode=True, crf=17, nvenc=False, preset='veryslow')
