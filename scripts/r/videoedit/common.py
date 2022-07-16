import os

apis = {}
on_api_func = None
force = False


def on_api(func):
    global on_api_func
    on_api_func = func


def api(f, optional=False):
    def api_wrapper(*args, **kwargs):
        if (optional and force) or (not optional):
            on_api_func(f.__name__)
            f(*args, **kwargs)

    apis[f.__name__] = api_wrapper
    return api_wrapper


def get_apis():
    return apis


def find_vproject_root():
    path = os.getcwd()

    while os.path.dirname(path) != path:
        path = os.path.abspath(path + "/../")  # parent path
        if os.path.exists(os.path.join(path, ".vproject")):
            return path


class VideoEditException(Exception):
    pass
