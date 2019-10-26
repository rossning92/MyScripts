from _shutil import *
from _term import *


def install_gdrive():
    make_and_change_dir(r'C:\tools\gdrive')

    if not exists('gdrive.exe'):
        print2('Downloading gdrive.exe ...')
        download('https://github.com/gdrive-org/gdrive/releases/download/2.1.0/gdrive-windows-x64.exe',
                 filename='gdrive.exe')


def read_table(str):
    lines = str.split('\n')
    header = lines[0]

    pos = []  # start position of each column
    for i in range(len(header)):
        if i == 0 or (header[i - 1] == ' ' and header[i] != ' '):
            pos.append(i)

    table = []
    for i in range(1, len(lines)):
        if lines[i] == '':
            continue

        row = []
        for j in range(len(pos) - 1):
            field = lines[i][pos[j]: pos[j + 1]].strip()
            row.append(field)

        table.append(row)

    return table


def get_file_id(name):
    s = Popen('gdrive list --name-width 0 -q "trashed = false and \'root\' in parents"',
              stdout=subprocess.PIPE).stdout.read().decode('utf-8')

    table = read_table(s)

    for row in table:
        fileId = row[0]
        fileName = row[1]
        if fileName == name:
            print("FOUND: " + fileName + ' -> ' + fileId)
            return fileId

    return None


def create_dir(name):
    # get folder
    fileId = get_file_id(name)

    # create folder if it doesn't exist
    if fileId is None:
        s = Popen('gdrive mkdir "%s"' % name,
                  stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        print(s)
        fileId = s.split()[1]

    return fileId


if __name__ == '__main__':
    install_gdrive()

    path = env['CURRENT_FOLDER']
    print('Backup `%s`? (Y/N)' % path)
    if getch() != 'y':
        sys.exit(0)

    # mkdir('C:\\gdrive')
    # path = 'C:\\gdrive\\Notes'

    name = os.path.basename(path)
    fileId = create_dir(name)

    # sync
    call2('gdrive sync upload --delete-extraneous "%s" %s' % (path, fileId))
