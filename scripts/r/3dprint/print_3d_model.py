import os
import sys

from _shutil import write_temp_file
from ext.run_script_in_remote_shell import run_bash_script_in_remote_shell
from ext.run_script_ssh import push_file_putty, run_bash_script_putty

if __name__ == "__main__":
    # if there is no arguments
    if len(sys.argv) <= 1:
        file = "CCR10S_xyzCalibration_cube.gcode"
    else:
        file = sys.argv[1]

    if not file.endswith(".gcode"):
        raise Exception("Only gcode file is supported.")

    # Upload gcode file
    push_file_putty(file)
    dst = os.path.basename(file)

    # Print via pronsole
    bash = (
        "pronsole"
        " -e connect"
        " -e block_until_online"
        " -e gettemp"
        f' -e "load {dst}"'
        " -e print"
        " -e monitor"
        " -e exit"
    )
    print(bash)
    bash_file = write_temp_file(bash, ".sh")
    if os.environ.get("_RUN_IN_REMOTE_SHELL"):
        run_bash_script_in_remote_shell(bash_file)
    else:
        run_bash_script_putty(
            bash_file,
            host=os.environ["PRINTER_3D_HOST"],
            user=os.environ["PRINTER_3D_USER"],
            pwd=os.environ["PRINTER_3D_PWD"],
        )
