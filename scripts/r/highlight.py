import sys
import re
import argparse


# https://gist.github.com/dominikwilkowski/60eed2ea722183769d586c76f22098dd
# ANSI escape codes for colors
COLOR_MAP = {
    "black": "\u001b[30;1m",
    "blue": "\u001b[34;1m",
    "cyan": "\u001b[36;1m",
    "green": "\u001b[32;1m",
    "magenta": "\u001b[35;1m",
    "red": "\u001b[31;1m",
    "RED": "\u001b[41;1m",
    "white": "\u001b[37;1m",
    "yellow": "\u001b[33;1m",
    "YELLOW": "\u001b[43;1m",
}
RESET_ALL = "\033[0m"


def setup_console_colors():
    # Enable ANSI escape sequence processing for the console window by calling
    # the SetConsoleMode Windows API with the ENABLE_VIRTUAL_TERMINAL_PROCESSING
    # flag set.
    if sys.platform == "win32":
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)


def highlight(patterns={}):
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


parser = argparse.ArgumentParser()
parser.add_argument(
    "--patt",
    "-p",
    metavar="PATTERN=COLOR",
    nargs="+",
    help="provide pattern to color map",
)
args = parser.parse_args()
patt = parse_vars(args.patt)

setup_console_colors()
highlight(patterns=patt)
