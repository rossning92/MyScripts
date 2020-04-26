from _shutil import *
from _term import *

new_file = wait_for_new_file(os.path.expandvars(r"%USERPROFILE%\Videos\Desktop\*.mp4"))

name = input("input file name (no ext): ")
if not name:
    print2("Discard %s." % new_file, color="red")
    os.remove(new_file)

name = slugify(name)
os.makedirs("screencap", exist_ok=True)
dest_file = "screencap/" + name + ".mp4"
os.rename(new_file, dest_file)
print2("file saved: %s" % dest_file, color="green")

clip = "! screencap('%s')" % name + ".mp4"
set_clip(clip)
print("Clip is set to: %s" + clip)
wait_key()
