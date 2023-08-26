import argparse
import ctypes
import re
import signal
import sys

# https://gist.github.com/dominikwilkowski/60eed2ea722183769d586c76f22098dd
# ANSI escape codes for colors
COLOR_MAP = {
    "gray": "\u001b[90m",
    "blue": "\u001b[34m",
    "cyan": "\u001b[36m",
    "green": "\u001b[32m",
    "magenta": "\u001b[35m",
    "red": "\u001b[31m",
    "RED": "\u001b[41m",
    "white": "\u001b[37m",
    "yellow": "\u001b[33m",
    "YELLOW": "\u001b[43m",
}
RESET_ALL = "\033[0m"


class IgnoreSigInt(object):
    def __enter__(self):
        self.original_handler = signal.getsignal(signal.SIGINT)

        def handler(signum, frame):
            pass

        signal.signal(signal.SIGINT, handler)
        return self

    def __exit__(self, type, value, tb):
        signal.signal(signal.SIGINT, self.original_handler)


def setup_console_colors():
    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def highlight(patterns={}):
    with IgnoreSigInt():
        while True:
            line = sys.stdin.readline()
            if line == "":
                break
            else:
                line = line.rstrip("\n")

            index_color_list = []
            for patt, color in patterns.items():
                # Query ANSI character color codes
                if color in COLOR_MAP:
                    color = COLOR_MAP[color]

                for match in re.finditer(patt, line):
                    index_color_list.append((match.start(), color))
                    index_color_list.append((match.end(), None))
            index_color_list = sorted(index_color_list, key=lambda x: x[0])

            if len(index_color_list) > 0:
                color_stack = [RESET_ALL]
                indices, colors = zip(*index_color_list)
                parts = [line[i:j] for i, j in zip(indices, indices[1:] + (None,))]

                line = line[0 : indices[0]]
                for i in range(len(parts)):
                    if colors[i]:
                        line += colors[i]
                        color_stack.append(colors[i])
                    else:
                        color_stack.pop()
                        line += color_stack[-1]
                    line += parts[i]

            print(line)


def parse_var(s):
    """
    Parse a key, value pair, separated by '='
    That's the reverse of ShellArgs.

    On the command line (argparse) a declaration will typically look like:
        foo=hello
    or
        foo="hello world"
    """
    items = s.split("=")
    key = items[0].strip()  # we remove blanks around keys, as is logical
    if len(items) > 1:
        # rejoin the rest:
        value = "=".join(items[1:])
    return (key, value)


def parse_vars(items):
    """
    Parse a series of key-value pairs and return a dictionary
    """
    d = {}
    if items:
        for item in items:
            key, value = parse_var(item)
            d[key] = value
    return d


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--patt",
        "-p",
        metavar="PATTERN=COLOR",
        nargs="+",
        help="provide pattern to color map",
    )
    args = parser.parse_args()

    setup_console_colors()
    highlight(patterns=parse_vars(args.patt))
