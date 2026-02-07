import io
import traceback
from typing import Optional

from .menu import Menu


class ExceptionMenu(Menu[str]):
    def __init__(
        self,
        exception: Optional[Exception] = None,
        prompt="exception",
    ):
        self.__prompt = prompt

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
        super().__init__(
            prompt=self.__prompt,
            items=err_lines,
        )
