from _shutil import *
from _script import *

VERSION = '{{UE4_VERSION}}' if '{{UE4_VERSION}}' else '4.24'
PROJ_FOLDER = r'{{UE_SOURCE}}'
if not PROJ_FOLDER:
    PROJ_FOLDER = os.path.realpath(os.path.expanduser('~/Projects/UE' + VERSION))

set_variable('UE_SOURCE', PROJ_FOLDER)
make_and_change_dir(PROJ_FOLDER)

if '{{_OCULUS_BRANCH}}':
    url = 'https://github.com/Oculus-VR/UnrealEngine.git'
else:
    url = 'https://github.com/EpicGames/UnrealEngine.git'

call_echo(f'git clone -b {VERSION} --single-branch {url} --depth 1 .')
