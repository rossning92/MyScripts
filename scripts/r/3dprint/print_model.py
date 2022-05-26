import os
import sys

from _shutil import write_temp_file
from ext.run_script_ssh import run_bash_script_putty
from r.linux.push_file_ssh import push_file

if __name__ == "__main__":
    # if there is no arguments
    if len(sys.argv) == 1:
        file = "CCR10S_xyzCalibration_cube.gcode"
    else:
        file = sys.argv[1]

    if not file.endswith(".gcode"):
        raise Exception("Only .gcode is supported.")

    push_file(file)
    dst = os.path.basename(file)

    bash = (
        'pronsole -e "connect" -e "block_until_online" -e "gettemp" -e "load %s" -e "print"'
        % dst
    )
    print(bash)
    bash_file = write_temp_file(bash, ".sh")
    run_bash_script_putty(
        bash_file, ssh_pwd="{{SSH_PWD}}", user_host="{{SSH_USER}}@{{SSH_HOST}}"
    )
