from _shutil import *

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s_out.mp3' % fn

    args = [
        'ffmpeg',
        '-i', f]

    args += [
        '-codec:a', 'libmp3lame',
        '-qscale:a', '2']

    args += [out_file]

    subprocess.call(args)
