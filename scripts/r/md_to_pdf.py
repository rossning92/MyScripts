from _shutil import *
from r.open_with.open_with_ import open_with

setup_nodejs()

if r'{{MD_FILE}}':
    f = r'{{MD_FILE}}'
else:
    f = get_files()[0]


try:
    call2('mdpdf --version')
except:
    call_echo('yarn global add mdpdf')

call_echo('mdpdf "%s" --format=A5' % f)

open_with(os.path.splitext(f)[0] + '.pdf')
