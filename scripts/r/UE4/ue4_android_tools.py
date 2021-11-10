from _shutil import getch, print2
from _ue4 import ue4_command

commands = {
    "r": "vr.HeadTracking.Reset",
    "m": "ke * MoveCameraEvent",
    "[": "vr.PixelDensity 0.1",
    "]": "vr.PixelDensity 1.0",
    "1": "stat fps",  # stat RHI
    "2": "stat unit",
    "3": "stat RHI",
    "4": "stat GPU",
}

if __name__ == "__main__":
    while True:
        for k, v in commands.items():
            print("[%s] %s" % (k, v))
        print("[`] enter console command")

        s = getch()
        if s == "`":
            while True:
                print2("console> ", end="", color="green")
                cmd = input()
                if not cmd:
                    break

                ue4_command(cmd)

        elif s in commands:
            cmd = commands[s]
            print(cmd)
            ue4_command(cmd)
