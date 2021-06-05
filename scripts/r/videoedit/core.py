apis = {}
on_api_func = None


def on_api(func):
    global on_api_func
    on_api_func = func


def api(f):
    def api_wrapper(*args, **kwargs):
        on_api_func(f.__name__)
        f(*args, **kwargs)

    apis[f.__name__] = api_wrapper
    return api_wrapper


def get_apis():
    return apis

