import glob
import re
import os
from myutils import *

os.chdir('..')

patt = r'\[([a-zA-Z_][a-zA-Z_0-9]*)\]'

for f in glob.glob('**/*.*', recursive=True):
    file_name = os.path.basename(f)
    dir = os.path.dirname(f)

    flags = set(re.findall(patt, f))
    if len(flags) > 0:
        new_file_name = re.sub(patt, '', file_name)
        new_file_path = os.path.join(dir, new_file_name)

        # Create meta file
        meta = ScriptMeta(new_file_path)
        if 'run_as_admin' in flags:
            meta.meta['runAsAdmin'] = True
        if 'new_window' in flags:
            meta.meta['newWindow'] = True
        meta.save()

        # Rename file
        os.rename(f, new_file_path)
        print(new_file_path)
