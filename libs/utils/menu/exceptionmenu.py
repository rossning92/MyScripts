import io
import time
import traceback
from typing import Optional

from utils.menu import Menu


class ExceptionMenu(Menu[str]):
    def __init__(
        self,
        exception: Optional[Exception] = None,
        timeout=3,
        prompt="exception",
    ):
        self.should_retry = False

        self.__prompt = prompt

        self.__start_time = time.time()
        self.__timeout = float(timeout)

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
            prompt=(
                f"{self.__prompt} (retry in {timeout}s, esc to cancel)"
                if self.__timeout > 0.0
                else self.__prompt
            ),
            items=err_lines,
        )

    def on_idle(self):
        if self.__timeout > 0.0:
            now = time.time()
            if now > self.__start_time + self.__timeout:
                self.should_retry = True
                self.close()

    def on_escape_pressed(self):
        if self.__timeout > 0.0:
            self.should_retry = False
            self.set_prompt(self.__prompt)
        else:
            return super().on_escape_pressed()
