from _shutil import *

files = get_files(cd=True)

mkdir("out")
for f in files:
    if not os.path.isfile(f):
        continue

    name_no_ext, ext = os.path.splitext(f)
    out_file = f"out/{name_no_ext}.wav"

    args = ["ffmpeg", "-i", f]

    args += [out_file]

    subprocess.call(args)
