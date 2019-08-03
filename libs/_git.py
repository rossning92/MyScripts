from _shutil import *


def git_clone(url):
    proj_path = os.path.expanduser('~/Projects')
    make_and_change_dir(proj_path)
    folder_name = url.split('/')[-1]
    if not exists(folder_name):
        subprocess.check_call(['git', 'clone', url])
    else:
        print2("%s already exists. Don't clone" % folder_name)
    os.chdir(folder_name)
