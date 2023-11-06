from _shutil import *
from _video import *


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata

    value = unicodedata.normalize("NFKD", value)
    value = re.sub("[^\w\s-]", "", value).strip().lower()
    value = re.sub("[-\s]+", "-", value)
    return value


in_file = get_files(cd=True)[0]
name, ext = os.path.splitext(in_file)

ext = ".mp4"

start, duration = "{{_START_AND_DURATION}}".split()
out_file = name + f"_cut_{slugify(start)}_{slugify(duration)}" + ext

ffmpeg(in_file, out_file, start=float(start), duration=float(duration), reencode=True)
