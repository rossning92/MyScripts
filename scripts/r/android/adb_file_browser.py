from _shutil import *
from prompt_toolkit import prompt
from prompt_toolkit.completion import *


cur = '/sdcard'
save_path = os.path.expanduser(os.path.join('~', 'Desktop'))

while True:
    files = list(read_lines('adb shell "ls \'%s\'"' % cur))
    print('\n'.join(['@%d %s' % (i, x) for i, x in enumerate(files)]))

    input = prompt('%s > ' % cur, completer=FuzzyWordCompleter(files))
    if input == '':
        continue

    elif input == '..':
        cur = os.path.dirname(cur)
        continue

    elif input.startswith('@'):
        index = int(input[1:])
        selected = cur + '/' + files[index]

    else:
        selected = cur + '/' + input

    # check if it is a file
    if subprocess.call(['adb', 'shell', '[ -f "%s" ]' % selected]) == 0:
        print(selected)
        print('Pulling file %s...' % selected)
        subprocess.check_call(['adb', 'pull', selected, save_path])
    else:
        cur = selected
