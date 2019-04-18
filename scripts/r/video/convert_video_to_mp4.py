from _shutil import *

files = get_files(cd=True)

for f in files:
    if not os.path.isfile(f):
        continue

    name_no_ext = os.path.splitext(f)[0]
    out_file = 'out_%s.mp4' % name_no_ext

    args = [
        'ffmpeg',
        '-i', f,
        # '-filter:v', 'crop=200:200:305:86',
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '22',  # Lossless
        '-c:a', 'aac', '-b:a', '128k',
        out_file
    ]
    subprocess.call(args)
