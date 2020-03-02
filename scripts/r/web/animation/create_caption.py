import codecs
from _shutil import *

src = r"C:\Users\Ross\Google Drive\Notes\Kidslogic\Coding_in_3_minutes\ep13\ep13.md"
marker_file = r"C:\Data\ep13\Sequence 01.csv"


lines = open(src, encoding='utf-8').readlines()

lines = [x.strip() for x in lines]
lines = [x for x in lines if x and re.match('^[^#<!-]', x)]


marker = open(marker_file, encoding='utf-16').readlines()
marker = marker[1:]
marker = [x.split()[0] for x in marker]


with open('123.srt', 'w', encoding='utf-8') as f:
    f.write('\ufeff')

    last_ts = None
    for i, start_time in enumerate(marker):
        ms = int(start_time[9:11]) * 1000 // 25
        ms = '%03d' % ms
        end_ts = start_time[0:8] + ',' + ms

        if last_ts:
            f.write('%d\n' % i)
            f.write('%s --> %s\n' % (last_ts, end_ts))
            f.write('%s\n\n' % lines[i-1])

        last_ts = end_ts
