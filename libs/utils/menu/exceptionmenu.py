import io
import traceback

from utils.menu import Menu


class ExceptionMenu(Menu[str]):
    def __init__(self):
        output = io.StringIO()
        traceback.print_exc(file=output)
        err_lines = output.getvalue().splitlines()
        super().__init__(prompt="exception", items=err_lines)
