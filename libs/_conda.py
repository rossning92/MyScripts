def setup_env():
    from os import environ, pathsep
    from os.path import expanduser, exists, join
    import subprocess

    SEARCH_PATH = [
        '~/Anaconda3',
        r'C:\tools\miniconda3',
        r'C:\tools\anaconda3',
    ]

    for p in SEARCH_PATH:
        if exists(expanduser(p)):
            print("Found Anaconda3: " + p)
            conda_path = [
                expanduser(p),
                expanduser(join(p, 'Scripts'))
            ]

            # Prepend anaconda to PATH
            environ["PATH"] = pathsep.join(conda_path) + pathsep + environ["PATH"]
            break


setup_env()
