import io
import traceback
from typing import Optional

from utils.menu import Menu


class ExceptionMenu(Menu[str]):
    def __init__(self, exception: Optional[Exception] = None):
        output = io.StringIO()
        if exception:
            traceback.print_exception(
                type(exception),
                exception,
                exception.__traceback__,
                file=output,
            )
        else:
            traceback.print_exc(file=output)
        err_lines = output.getvalue().splitlines()
        super().__init__(prompt="exception", items=err_lines)
