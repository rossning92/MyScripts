from utils.getch import getch
from utils.printc import printc


def confirm(msg=""):
    msg += " (y/n): "
    printc(msg, end="", color="green")
    ch = getch()
    print()
    return ch == "y"
