import yaml
import shutil
from os.path import dirname, join


def get_executable(app_name):
    with open(join(dirname(__file__), 'app_list.yaml'), 'r') as f:
        app_list = yaml.load(f.read())

    matched_apps = [v for k, v in app_list.items() if app_name.lower() == k.lower()]
    app = matched_apps[0]

    executable = None
    for e in app['executable']:
        if shutil.which(e):
            executable = e
            break

    # TODO: install app

    print(executable)
    return executable


get_executable('7z')
