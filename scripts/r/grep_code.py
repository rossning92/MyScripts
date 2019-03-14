from _term import *
from _shutil import *
from _editor import *

SRC_DIR = r'{{SOURCE_FOLDER}}'

repo_root = None
rel_path = None

if False:
    tmp_path = ''
    for comp in SRC_DIR.split('\\'):
        tmp_path += comp + '\\'
        if exists(tmp_path + '.gitignore'):
            print('REPO ROOT: ' + tmp_path)
            repo_root = tmp_path
            rel_path = SRC_DIR.replace(repo_root, '')
            print(rel_path)
            break

    input()


def text_changed(s):
    global cur_text
    global ps

    cur_text = s
    if ps:
        ps.kill()
        ps = None


def item_selected(i):
    arr = lines[i].split(':')
    file = os.path.join(SRC_DIR, arr[0])
    line_no = arr[1]
    open_in_androidstudio(file, line_no)


ps = None
lines = []
files = set()
cur_text = None
if repo_root:
    chdir(repo_root)
else:
    chdir(SRC_DIR)
lw = ListWidget(lines=lines, text_changed=text_changed, item_selected=item_selected)

text = None
while True:
    while cur_text == text:
        time.sleep(0.1)
        lw.update()
    text = cur_text

    if text == '':
        lines.clear()
        continue

    args = f'rg --line-number -F "{text}"'
    if rel_path:
        args += ' ' + rel_path
    args += ' -g "!intermediates/" -g "!build/"'

    ps = check_output2(args)

    lines.clear()
    files.clear()
    for l in ps.readlines():
        s = l.decode(errors='replace')
        s = s.strip()
        lines.append(s)

        lw.update()
