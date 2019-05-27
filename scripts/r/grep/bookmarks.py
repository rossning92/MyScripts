from _grep import *
import yaml
import json


def parse_bookmarks(file):  # parse .md file
    with open(file, encoding='utf-8') as f:
        lines = f.readlines()

    lines.append('name: <FOR EVALUATING LAST VALUE>')

    bookmarks = []
    cur_vals = {}
    for line in lines:
        line = line.rstrip('\n').rstrip('\r')

        match = re.match('^(name|kw|path)\s*:\s*(.*)', line)
        if match:
            key = match.group(1)
            val = match.group(2)

            if val == 'path':  # `path` should be a list
                val = val.split('|')

            if key == 'name':  # Store last parsed bookmark
                if 'name' in cur_vals:  # not empty
                    bookmarks.append(cur_vals)
                    cur_vals = {k: v for k, v in cur_vals.items() if k == 'path'}  # keep only `path` value

            cur_vals[key] = val

    return bookmarks

if __name__ == '__main__':
    bookmarks = []
    for f in glob.glob('../../../data/grep/*.md'):
        f = os.path.abspath(f)
        bookmarks += parse_bookmarks(f)

    show_bookmarks(bookmarks=bookmarks)
