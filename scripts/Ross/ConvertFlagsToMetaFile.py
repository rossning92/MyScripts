import glob
import re
import os

os.chdir('..')

patt = r'\[([a-zA-Z_][a-zA-Z_0-9]*)\]'

for f in glob.glob('**/*.*'):
    file_name = os.path.basename(f)

    flags = set(re.findall(patt, f))

    if len(flags) > 0:
        file_name = re.sub(patt, '', file_name)
        print(file_name)