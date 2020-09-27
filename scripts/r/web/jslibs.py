from _shutil import *


def print_help():
    print("d - dat.gui\n" "p - p5\n" "h - help\n" "x - exit\n")


project_dir = get_current_folder()
chdir(project_dir)

print2("Project dir: %s" % project_dir)
print_help()
while True:
    ch = getch()
    if ch == "x":
        sys.exit(0)
    elif ch == "d":
        call_echo("yarn add dat.gui")
    elif ch == "p":
        call_echo("yarn add p5")
    elif ch == "h":
        print_help()
