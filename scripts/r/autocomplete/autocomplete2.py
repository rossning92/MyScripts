from _shutil import *
from _term import *

lines = open("WordList.txt").read().splitlines()
lines = [x for x in lines if x.strip() != ""]

kw = [x.split("|")[0] for x in lines]
completion = [x.split("|")[-1] for x in lines]

index = ListWindow(kw).exec()

if index < -1:
    sys.exit(0)

set_clip(completion[index])
