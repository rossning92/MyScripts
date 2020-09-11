from _shutil import *


project_dir = get_current_folder()
chdir(project_dir)

print2("Project dir: %s" % project_dir)
while True:
    ch = getch()
    if ch == "x":
        sys.exit(0)
    elif ch == "d":
        call_echo("yarn add dat.gui")
