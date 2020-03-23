from _shutil import *

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    fn, ext = os.path.splitext(f)
    out_file = '%s.out.m4a' % fn

    args = [
        'ffmpeg',
        '-i', f]

    args += [
        '-codec:a', 'aac',
        '-b:a', '160k']

    args += [out_file]

    subprocess.call(args)
