import os
import subprocess

from _script import Script
from _shutil import call_echo, convert_to_unix_path, print2, wait_key, write_temp_file

TEMP_SHELL_SCRIPT_PATH = "/tmp/tmp_script.sh"


def plink_run_bash_script(bash_script_file, user_host, ssh_port=None, ssh_pwd=None):
    # plink is preferred (better automation)
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    args = f"plink -ssh -t {user_host} -m {bash_script_file}"
    if ssh_pwd:
        args += " -pw %s" % ssh_pwd
    if ssh_port:
        args += " -P %d" % ssh_port
    try:
        call_echo(args)
    except subprocess.CalledProcessError:
        raise Exception("Remote shell returns non zero.")


def ssh_exec_command(user_host, command):
    call_echo(["wsl", "ssh", user_host, command])


def ssh_run_bash_script(bash_script_file, user_host, ssh_port=None, ssh_pwd=None):
    call_echo(
        [
            "wsl",
            "scp",
            convert_to_unix_path(bash_script_file, wsl=True),
            user_host + ":/tmp/s.sh",
        ]
    )
    # -t : interactive session
    call_echo(
        ["wsl", "ssh", "-t", user_host, "source ~/.bash_profile ; bash /tmp/s.sh"]
    )
    if wait_key("press any key to pause"):
        input("press any key to exit...")


def run_bash_script_vagrant(bash_script_file, vagrant_id):
    call_echo(
        f"vagrant upload {bash_script_file} {TEMP_SHELL_SCRIPT_PATH} {vagrant_id}"
    )
    call_echo(f'vagrant ssh -c "bash {TEMP_SHELL_SCRIPT_PATH}" {vagrant_id}')


if __name__ == "__main__":
    script_path = os.environ["_SCRIPT"]
    if script_path.endswith("run_script_remotely.py"):
        print("Parameter saved...")
        exit(0)

    script = Script(script_path)
    # update_script_acesss_time(script)
    tmp_script_file = write_temp_file(script.render(), ".sh")

    if script.ext == ".sh":
        if "{{VAGRANT_ID}}":
            run_bash_script_vagrant(tmp_script_file, "{{VAGRANT_ID}}")
        else:
            ssh_port = None
            ssh_pwd = None
            try:
                ssh_host = os.environ["_SSH_HOST_"]
                ssh_port = int(os.environ["_SSH_PORT_"])
                ssh_pwd = os.environ["_SSH_PWD_"]
            except KeyError:
                ssh_host = "{{SSH_USER}}@{{SSH_HOST}}"
                ssh_port = int("{{SSH_PORT}}") if "{{SSH_PORT}}" else None
                ssh_pwd = r"{{SSH_PWD}}" if r"{{SSH_PWD}}" else None

            ssh_run_bash_script(tmp_script_file, ssh_host, ssh_port, ssh_pwd=ssh_pwd)

    else:
        print2("script extension not supported: %s" % script.ext, color="red")
