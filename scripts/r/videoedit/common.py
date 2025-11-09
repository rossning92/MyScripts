import math
import os
import time

apis = {"ceil": math.ceil, "floor": math.floor}
on_api_func = None
force = False


def on_api(func):
    global on_api_func
    on_api_func = func


def api(f, skip=False):
    def api_wrapper(*args, **kwargs):
        if force or (not skip):
            on_api_func(f.__name__)
            return f(*args, **kwargs)

    apis[f.__name__] = api_wrapper
    return api_wrapper


def get_apis():
    return apis


def find_vproject_root():
    path = os.getcwd()

    while os.path.dirname(path) != path:
        path = os.path.abspath(path + "/../")  # parent path
        if os.path.basename(path) == "vprojects":
            return path


@api
def sleep(secs):
    time.sleep(secs)


class VideoEditException(Exception):
    pass
