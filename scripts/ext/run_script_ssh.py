import os
import subprocess

from _script import Script, get_variable
from _shutil import call_echo, convert_to_unix_path, print2, wait_key, write_temp_file

TEMP_SHELL_SCRIPT_PATH = "/tmp/tmp_script.sh"


def run_bash_script_plink(
    bash_script_file, user_host=None, ssh_port=None, ssh_pwd=None
):
    if ssh_pwd is None:
        ssh_pwd = get_variable("SSH_PWD")
    if user_host is None:
        user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    # plink is preferred for automation.
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    args = f"plink -ssh -t -no-antispoof {user_host} -m {bash_script_file}"
    if ssh_pwd:
        args += " -pw %s" % ssh_pwd
    if ssh_port:
        args += " -P %d" % ssh_port
    try:
        call_echo(args)
    except subprocess.CalledProcessError:
        raise Exception("Remote shell returns non zero.")


def run_bash_script_ssh(
    bash_script_file, user_host, ssh_port=None, ssh_pwd=None, wsl=False
):
    call_echo(
        (["wsl"] if wsl else [])
        + [
            "scp",
            convert_to_unix_path(bash_script_file, wsl=True)
            if wsl
            else bash_script_file,
            user_host + ":/tmp/s.sh",
        ]
    )
    # -t : interactive session
    # source ~/.bash_profile ;
    call_echo((["wsl"] if wsl else []) + ["ssh", "-t", user_host, "bash /tmp/s.sh"])
    if wait_key("press any key to pause...", timeout=5):
        input("press any key to exit...")


def run_bash_script_vagrant(bash_script_file, vagrant_id):
    call_echo(
        f"vagrant upload {bash_script_file} {TEMP_SHELL_SCRIPT_PATH} {vagrant_id}"
    )
    call_echo(f'vagrant ssh -c "bash {TEMP_SHELL_SCRIPT_PATH}" {vagrant_id}')


if __name__ == "__main__":
    script_file = os.environ["_SCRIPT"]

    script = Script(script_file)
    tmp_script_file = write_temp_file(script.render(), ".sh")

    if script.ext == ".sh":
        ssh_port = None
        ssh_pwd = get_variable("SSH_PWD")
        ssh_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

        run_bash_script_ssh(tmp_script_file, ssh_host, ssh_port, ssh_pwd=ssh_pwd)

    else:
        print2("script extension not supported: %s" % script.ext, color="red")
