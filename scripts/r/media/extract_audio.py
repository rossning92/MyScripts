from _shutil import *

in_file = get_files(cd=True)[0]

args = []
args += ["ffmpeg", "-i", in_file]
args += ["-map_channel", "0.1.1"]

if '{{_FORMAT_WAV}}':
    out_file = os.path.splitext(in_file)[0] + '.wav'
    args += [out_file]
else:
    out_file = os.path.splitext(in_file)[0] + '.mp3'
    args += ["-vn", "-acodec", "mp3", out_file]

call2(args)
