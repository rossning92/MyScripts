import atexit
import hashlib
import json
import os


def get_hash(o):
    return hashlib.md5(repr(o).encode("utf-8")).hexdigest()


def file_cache(func):
    cache_file = "tmp/cache_%s.json" % func.__name__
    cache = None

    def get_cache():
        nonlocal cache
        if cache is None:
            if os.path.exists(cache_file):
                cache = json.load(open(cache_file, "r"))
            else:
                cache = {}

        return cache

    def dump_cache():
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(cache, f, indent=2)

    def memoized_func(*args, **kwargs):
        cache = get_cache()

        h = get_hash((args, kwargs))

        if h in cache:
            return cache[h]
        else:
            result = func(*args, **kwargs)
            cache[h] = result
            dump_cache()
            return result

    return memoized_func
