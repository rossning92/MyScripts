"""
ref: https://github.com/Xunius/markdown2zim
"""

import re
import os
import glob
import sys


def replace_title(s):
    for i in range(6):
        equal_sign = '=' * (6 - i)
        sharp_sign = '#' * (i + 1)
        patt = r'^' + equal_sign + ' (.*?) ' + equal_sign + '$'
        repl = sharp_sign + r' \1'
        s = re.sub(patt,
                   repl,
                   s,
                   flags=re.MULTILINE)
    return s


def convert_to_md(file_path):
    #print('Converting: %s' % file_path)

    with open(file_path, encoding='utf-8') as f:
        s = f.read()

    s = replace_title(s)
    # s = re.sub('//(.*?)//', r'\*\1\*', s)

    # Images
    base_name = os.path.basename(os.path.splitext(file_path)[0])
    s = re.sub(r'\{\{\.[/\\](.*?)\}\}', r'![](%s/\1)' % base_name, s)

    # Links
    s = re.sub(r'\[\[\+(.*?)\]\]', lambda x: r'[%s](%s/%s.md)' % (x.group(1), base_name, x.group(1).replace(' ', '_')),
               s)
    # s = re.sub(r'\[\[\./(.*?)\]\]', r'[File](\1)', s)

    file_md = os.path.splitext(file_path)[0] + '.md'

    existing_content = None
    if os.path.exists(file_md):
        existing_content = open(file_md, 'r', encoding='utf-8').read()

    if s != existing_content:
        print('Output: %s' % file_md)
        with open(file_md, 'w', encoding='utf-8') as f:
            f.write(s)


os.chdir(r'E:\Documents\Notes')

for f in glob.glob('**/*.txt', recursive=True):
    convert_to_md(f)
