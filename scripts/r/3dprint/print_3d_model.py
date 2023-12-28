import argparse
import os

from _shutil import write_temp_file
from ext.run_script_remotely import run_bash_script_in_remote_shell
from ext.run_script_ssh import push_file, run_script

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str)
    args = parser.parse_args()

    file = args.file
    if not file.lower().endswith(".gcode"):
        raise Exception("Only gcode file is supported.")

    # Upload gcode file
    push_file(
        file,
        host=os.environ["PRINTER_3D_HOST"],
        user=os.environ["PRINTER_3D_USER"],
        pwd=os.environ["PRINTER_3D_PWD"],
    )
    dst = os.path.basename(file)

    # Print gcode using pronsole
    bash = (
        "pronsole"
        " -e connect"
        " -e block_until_online"
        " -e gettemp"
        f' -e "load {dst}"'
        ' -e "M140 S50"'  # set bed temperature to 50 degrees
        ' -e "M104 S200"'  # set extruder temprature to 200 degrees
        " -e print"
    )

    # Always run in a screen session to avoid interruption of printing due to
    # SSH disconnection.
    bash = (
        "export TERM=xterm-256color;"
        f"screen -ls 3dp && screen -r 3dp || screen -mS 3dp bash -c '{bash}'"
    )

    print(bash)
    bash_file = write_temp_file(bash, ".sh")
    if os.environ.get("_RUN_IN_REMOTE_SHELL"):
        run_bash_script_in_remote_shell(bash_file)
    else:
        run_script(
            bash_file,
            host=os.environ["PRINTER_3D_HOST"],
            user=os.environ["PRINTER_3D_USER"],
            pwd=os.environ["PRINTER_3D_PWD"],
        )
