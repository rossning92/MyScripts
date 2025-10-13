import logging


def retry(times=3, exceptions=(Exception,)):
    def decorator(func):
        def newfn(*args, **kwargs):
            attempt = 0
            while attempt < times:
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    logging.error(
                        "Error on running %s, attempt "
                        "%d of %d" % (func, attempt + 1, times)
                    )
                    attempt += 1
            return func(*args, **kwargs)

        return newfn

    return decorator
