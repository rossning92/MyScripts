def get_conda_path():
    from os import pathsep
    from os.path import expanduser, exists, join

    SEARCH_PATH = [
        '~/Anaconda3',
        r'C:\tools\miniconda3',
        r'C:\tools\anaconda3',
    ]

    for p in SEARCH_PATH:
        p = expanduser(p)
        if exists(p):
            print("Found Anaconda3: " + p)
            return p

    return None


def setup_env():
    from os import environ as env, pathsep
    from os.path import join

    conda_path = get_conda_path()
    assert conda_path is not None
    conda_path = [conda_path, join(conda_path, 'Scripts')]
    env['PATH'] = pathsep.join(conda_path) + pathsep + env['PATH']
