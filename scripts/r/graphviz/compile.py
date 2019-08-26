from _shutil import *
import re


def convert(src):
    out = os.path.splitext(src)[0] + '.txt'

    with open(src, 'r') as f:
        s = f.read()
    s = re.sub(r'^([ \t]*)cluster (.*?) {', r'\1subgraph "cluster \2" {\n\1\1label="\2"\n', s, flags=re.MULTILINE)

    with open(out, 'w') as f:
        f.write(s)

    return out


chdir(r'{{GRAPHVIZ_SRC_FOLDER}}')
files = list(glob.glob('**/*.dot', recursive=True))
files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
src_file = files[0]

src_file = convert(src_file)

formats = ['png']
for fmt in formats:
    dst_file = os.path.splitext(src_file)[0] + f'.{fmt}'

    call(f'cmd /c dot -T{fmt} "{src_file}" -o "{dst_file}"')

    if fmt == 'png':
        Popen([r"C:\Program Files\IrfanView\i_view64.exe", os.path.abspath(dst_file)])
