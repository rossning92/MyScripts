from _appmanager import *
from _shutil import *

_7z = get_executable('7z')
zip_file = get_files(cd=True)[0]
out_folder = os.path.splitext(zip_file)[0]
args = [
    _7z,
    'x',  # Extract
    '-aoa',  # Overwrite all existing files
    '-o' + out_folder,  # Out folder
    zip_file,
]
call2(args)
