import logging
from functools import wraps
from time import time


def timed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        elapsed = time() - start
        logging.debug("%s took %.3f time to finish" % (f.__name__, elapsed))
        return result

    return wrapper
