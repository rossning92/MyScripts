from _shutil import *
from _term import *
import r.audio.postprocess as pp


def get_recording_files(md_file):
    s = open(md_file, 'r', encoding='utf-8').read()
    matches = re.findall(r"record\('([\w\W]+?)'\)", s)
    matches = [x.strip() for x in matches]
    return matches


def export_recordings():
    recordings = get_recording_files('index.md')
    recordings = [('record/' + x) for x in recordings]
    print(recordings)

    all_recordings = map(lambda x: x.replace('\\', '/'),
                         glob.glob(os.path.join('record', '*.wav')))

    unused_files = sorted(list(set(all_recordings) - set(recordings)))
    print('\n'.join(unused_files))
    if unused_files and yes('remove unused recordings?'):
        for x in unused_files:
            os.remove(x)

    pp.create_final_vocal(file_list=recordings)


export_recordings()
