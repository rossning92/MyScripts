import os
import subprocess
import sys
import time

from _term import Menu

menu = Menu()

f = sys.argv[-1]


def grep(kw):
    args = f"grep -E '{kw}' '{f}' | less -iNS"
    print(args)
    subprocess.call(args, shell=True)


@menu.item()
def test():
    subprocess.call(f"lnav -i logcat.json", shell=True)
    subprocess.call(f"lnav '{f}'", shell=True)


@menu.item()
def anr_deadlock():
    grep("- (lock|wait)")


@menu.item()
def anr_traces():
    grep("/data/anr")


@menu.item()
def am_focused_activity():
    grep("am_focused_activity")


while True:
    menu.exec()
