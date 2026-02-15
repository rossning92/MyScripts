import traceback
from typing import Callable, Optional

from .menu import Menu


class ExceptionMenu(Menu[str]):
    @staticmethod
    def retry(func: Callable):
        while True:
            try:
                return func()
            except Exception as e:
                m = ExceptionMenu(e, "Exception ([r]etry)")
                m.exec()
                if not m.should_retry:
                    return

    def __init__(
        self,
        exception: Optional[Exception] = None,
        prompt="exception",
    ):
        self.should_retry = False
        if exception:
            err_lines = "".join(traceback.format_exception(exception)).splitlines()
        else:
            err_lines = traceback.format_exc().splitlines()

        super().__init__(prompt=prompt, items=err_lines)

        self.add_command(self.__retry, hotkey="r")

    def __retry(self):
        self.should_retry = True
        self.close()
