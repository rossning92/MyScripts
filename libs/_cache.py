import atexit
import hashlib
import json
import os


def file_cache(cache_file=None, check_modify=[]):
    def decorator(func):
        nonlocal cache_file
        if cache_file is None:
            os.makedirs("tmp", exist_ok=True)
            cache_file = "tmp/cache_%s.json" % func.__name__

        try:
            cache = json.load(open(cache_file, "r"))
            cache = {int(k): v for k, v in cache.items()}
        except (IOError, ValueError):
            cache = {}

        atexit.register(lambda: json.dump(cache, open(cache_file, "w"), indent=2))

        def memoized_func(*args):
            h = hash(args)

            if h in cache:
                return cache[h]
            else:
                result = func(*args)
                cache[h] = result
                return result

        return memoized_func

    return decorator
