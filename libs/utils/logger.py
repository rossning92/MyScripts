import logging
import os
from typing import Optional


def setup_logger(
    level: int = logging.INFO,
    log_to_stderr: bool = True,
    log_file: Optional[str] = None,
):
    format = (
        "%(asctime)s.%(msecs)03d %(levelname).1s "
        # "%(filename)-10s: "
        # "%(funcName)-10s: "
        "%(message)s"
    )
    datefmt = "%H:%M:%S"
    if log_to_stderr:
        logging.basicConfig(
            format=format,
            datefmt=datefmt,
            level=logging.DEBUG,
        )
    elif log_file:
        logging.basicConfig(
            filename=log_file,
            filemode="w",
            format=format,
            datefmt=datefmt,
            level=logging.DEBUG,
        )


if os.environ.get("_LOG"):
    setup_logger()
elif os.environ.get("_DEBUG"):
    setup_logger(level=logging.DEBUG)
