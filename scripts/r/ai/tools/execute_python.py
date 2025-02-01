import io
from contextlib import redirect_stderr, redirect_stdout

from utils.exec_then_eval import exec_then_eval


def execute_python(code: str) -> str:
    """Execute supplied python code.
    - Avoid using third-party libraries.
    - Don't add any comments into the code.
    """
    with io.StringIO() as buf, redirect_stdout(buf), redirect_stderr(buf):
        return_val = exec_then_eval(code, globals={})
        stdout = buf.getvalue()
        if return_val is not None or stdout:
            output = ""
            if stdout:
                output += stdout
            if return_val is not None:
                if output:
                    output += "\n"
                output += str(return_val)
            return output
        else:
            return "Python code finishes successfully."
