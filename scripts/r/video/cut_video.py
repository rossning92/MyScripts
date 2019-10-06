from _shutil import *


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', str(value)).strip().lower()
    value = re.sub('[-\s]+', '-', str(value))
    return value


in_file = get_files(cd=True)[0]
name, ext = os.path.splitext(in_file)

ext = '.mp4'
reencode = '-c:v libx264 -preset slow -crf 19'

start, duration = '{{_START_AND_DURATION}}'.split()
out_file = name + f'_cut_{slugify(start)}_{slugify(duration)}' + ext

call2(f'ffmpeg -i "{in_file}" -ss {start} -strict -2 -t {duration} {reencode} "{out_file}"')
