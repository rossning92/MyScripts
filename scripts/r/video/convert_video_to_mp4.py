from _shutil import *

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s_out.%s' % (fn, '.mp4')

    args = [
        'ffmpeg',
        '-i', f]

    if '{{_480P}}':
        args += ['-s', 'hd480']

    args += [
        # '-filter:v', 'crop=200:200:305:86',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '22',  # Lossless
        '-c:a', 'aac', '-b:a', '128k',
        out_file]

    subprocess.call(args)
