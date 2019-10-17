from _shutil import *

version = '{{UE4_VERSION}}' if '{{UE4_VERSION}}' else '4.23'
src_folder = r'{{UE_SOURCE}}'

make_and_change_dir(src_folder)

if '{{_OCULUS_BRANCH}}':
    url = 'https://github.com/Oculus-VR/UnrealEngine.git'
else:
    url = 'https://github.com/EpicGames/UnrealEngine.git'

call_echo(f'git clone -b {version} --single-branch {url} --depth 1 .')
