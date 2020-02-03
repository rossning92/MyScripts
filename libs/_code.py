from _shutil import *

modified_sources = set()


def _revert_file(file):
    print2('Reverting: %s' % file, color='red')
    subprocess.check_call(['hg', 'revert', file])


def insert_code(file, regex, code, mode="after"):
    file = os.path.realpath(file)

    if file not in modified_sources:
        _revert_file(file)
        modified_sources.add(file)

    s = open(file, 'rU').read()

    matches = re.findall('^.*' + regex + '.*$', s, re.MULTILINE)
    if not matches:
        print2('ERROR: fail to locate code:\n%s' % regex, color='red')
        sys.exit(1)

    print2('Patching: %s:' % file, color='magenta')
    for match in matches:
        if mode == 'after':
            print(match.strip())
        print2('+ ' + code.strip().splitlines()[0].strip(), color='green')
        if mode == 'before':
            print(match.strip())

    for match in set(matches):
        if mode == 'after':
            s = re.sub(re.escape(match), match + '\n' + code, s)
        elif mode == 'before':
            s = re.sub(re.escape(match), code + '\n' + match, s)
        else:
            raise Exception('wrong value in mode param')

    open(file, 'w', newline='\n').write(s)


def append_code(file, regex, code):
    insert_code(file, regex, code, mode='after')


def prepend_code(file, regex, code):
    insert_code(file, regex, code, mode='before')
