from _shutil import *
from _term import *
import r.audio.postprocess as pp


def get_meta_data(file, type_):
    s = open(file, 'r', encoding='utf-8').read()
    matches = re.findall('<!-- ' + type_ + r'([\w\W]+?)-->', s)
    matches = [x.strip() for x in matches]
    return matches


def export_recordings():
    recordings = get_meta_data('index.md', 'record:')

    all_recordings = map(lambda x: x.replace('\\', '/'),
                         glob.glob(os.path.join('record', '*.wav')))

    unused_files = sorted(list(set(all_recordings) - set(recordings)))
    print('\n'.join(unused_files))
    if unused_files and yes('remove unused recordings?'):
        for x in unused_files:
            os.remove(x)

    pp.create_final_vocal(file_list=recordings)


export_recordings()
