from _gui import *
from _shutil import *


def search_code(text, search_path, extra_params=None):
    args = [
        'rg',
        '-g', '!ThirdParty/', '-g', '!Extras/', '-g', '!Plugins/',
        '-F', text, '--line-number'
    ]
    if extra_params:
        args += extra_params
    # print(args)
    out = subprocess.check_output(args, shell=True, stderr=subprocess.PIPE, cwd=search_path)
    out = out.decode()
    print(out)

    result = []
    lines = out.split('\n')
    for line in lines:
        if line.strip() == '':
            continue
        arr = line.split(':')
        file_path = os.path.join(search_path, arr[0])
        line_no = arr[1]
        result.append((file_path, line_no))

    return result


def goto_code(file, line_no=None):
    args = [r'C:\Program Files\Android\Android Studio\bin\studio64.exe']
    if line_no is not None:
        args += ['--line', str(line_no)]
    args.append(file)

    subprocess.Popen(args)
    exec_ahk('WinActivate ahk_exe studio64.exe')


def goto_code(file, line_no=None):
    vscode = r'C:\Program Files\Microsoft VS Code\Code.exe'
    if line_no is None:
        subprocess.Popen([vscode, file])
    else:
        subprocess.Popen([vscode, f'{file}:{line_no}', '-g'])


def show_bookmarks(data):
    names = [x['name'] for x in data['bookmarks']]
    idx = search(names)
    if idx == -1:
        sys.exit(1)

    bookmark = data['bookmarks'][idx]

    if 'code' in bookmark:
        result = []
        if 'path' in bookmark:
            # Allow both str of list of str
            if type(bookmark['path']) == str:
                path_list = [bookmark['path']]
            elif type(bookmark['path']) == list:
                path_list = bookmark['path']
            else:
                raise Exception('Invalid value in `path`.')

            for path in path_list:
                if os.path.isdir(path):  # directory
                    result += search_code(text=bookmark['code'], search_path=path)
                else:  # file or glob
                    dir_path = os.path.dirname(path)
                    file_name = os.path.basename(path)

                    result += search_code(text=bookmark['code'],
                                          search_path=dir_path,
                                          extra_params=['-g', file_name])

        else:
            if os.path.exists(data['path']):
                result += search_code(text=bookmark['code'], search_path=data['path'])

        if len(result) == 1:
            goto_code(result[0][0], result[0][1])
        elif len(result) > 1:
            indices = select_options([f'{x[0]}:{x[1]}' for x in result])
            i = indices[0]
            goto_code(result[i][0], result[i][1])
    else:
        goto_code(bookmark['path'])


if __name__ == '__main__':
    goto_code(sys.argv[1])
