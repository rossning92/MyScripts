from _appmanager import *
from _shutil import *

file = get_files(cd=True)[0]

if file.endswith('.tar.gz'):
    output_dir = file.rstrip('.tar.gz')
    mkdir(output_dir)
    call2('tar xzvf "%s" -C "%s"' % (file, output_dir))

else:
    _7z = get_executable('7z')

    out_folder = os.path.splitext(file)[0]
    args = [
        _7z,
        'x',  # Extract
        '-aoa',  # Overwrite all existing files
        '-o' + out_folder,  # Out folder
        file,
    ]
    call2(args)
