from _shutil import *
from _term import *
from _ue4 import *

commands = {
    "r": "vr.HeadTracking.Reset",
    "m": "ke * MoveCameraEvent",
    "[": "vr.PixelDensity 0.1",
    "]": "vr.PixelDensity 1.0",
    "f": "stat fps", # stat RHI
    "u": "stat unit",
}

# Engine\Build\Android\Java\src\com\epicgames\ue4\ConsoleCmdReceiver.java
while True:
    for k, v in commands.items():
        print("%s - %s" % (k, v))

    s = getch()
    if s == "\r":
        print2("Console command: ", end="")
        cmd = input()
    elif s in commands:
        cmd = commands[s]
    else:
        cmd = s

    print(cmd)

    # print2('Run Command: %s' % cmd)
    ue4_command(cmd)
