from _shutil import *


args = ["scrcpy", "--always-on-top", "--window-x", "20", "--window-y", "20"]
if "{{_SIZE}}":
    args += ["--max-size", "{{_SIZE}}"]

call_echo(args)
