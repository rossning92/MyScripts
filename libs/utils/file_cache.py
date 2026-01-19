import functools
import hashlib
import json
import os
import time

CACHE_EXPIRATION_SECONDS = 86400  # 1 day


def file_cache(cache_dir_name: str, expiration_seconds: int = CACHE_EXPIRATION_SECONDS):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a unique key based on function name and arguments
            key_data = {"func": func.__name__, "args": args, "kwargs": kwargs}
            key_json = json.dumps(key_data, sort_keys=True)
            url_hash = hashlib.sha256(key_json.encode()).hexdigest()

            cache_dir = os.path.join(os.getcwd(), "tmp", cache_dir_name)
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(cache_dir, url_hash)

            if os.path.exists(cache_file):
                mtime = os.path.getmtime(cache_file)
                if time.time() - mtime < expiration_seconds:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        return f.read()

            result = func(*args, **kwargs)

            # For now, only cache string results
            if isinstance(result, str):
                with open(cache_file, "w", encoding="utf-8") as f:
                    f.write(result)

            return result

        return wrapper

    return decorator
