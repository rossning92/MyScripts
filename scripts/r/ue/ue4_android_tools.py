from _shutil import menu_item, menu_loop, print2
from _ue4 import ue4_command
from utils.android import restart_current_app

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


@menu_item(key="`")
def console_command():
    while True:
        print2("console> ", end="", color="green")
        cmd = input()
        if not cmd:
            break

        ue4_command(cmd)


msaa_levels = [1, 2, 4]
cur_msaa_index = 0


@menu_item(key="m")
def toggle_msaa():
    global cur_msaa_index
    ue4_command("r.MobileMSAA %d" % msaa_levels[cur_msaa_index])
    cur_msaa_index = (cur_msaa_index + 1) % len(msaa_levels)


pixel_densities = [0.5, 0.75, 1, 1.25, 1.5, 2]
current_pd_index = 0


@menu_item(key="p")
def toggle_pixel_density():
    global current_pd_index
    ue4_command("vr.PixelDensity %g" % pixel_densities[current_pd_index])
    current_pd_index = (current_pd_index + 1) % len(pixel_densities)


headlock = 0


@menu_item(key="H")
def toggle_headlock():
    global headlock
    headlock = 1 - headlock
    ue4_command("ovr.HeadLock %d" % headlock)


@menu_item(key="R")
def restart_cur_app():
    global cur_msaa_index
    restart_current_app()


if __name__ == "__main__":
    menu_loop()
