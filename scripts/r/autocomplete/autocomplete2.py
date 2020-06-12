from _shutil import *
from _term import *

if os.path.exists("WordList.txt"):
    lines = open("WordList.txt").read().splitlines()
else:
    lines = ["Hello", "World", "This is test data"]

lines = [x for x in lines if x.strip() != ""]

kw = [x.split("|")[0] for x in lines]
completion = [x.split("|")[-1] for x in lines]

index = ListWindow(kw).exec()

if index < -1:
    sys.exit(0)

set_clip(completion[index])
