import argparse
import os
import subprocess

from _script import Script, get_variable
from _shutil import call_echo, convert_to_unix_path, wait_key, write_temp_file


def push_file_ssh(file, dst=None):
    if dst is None:
        dst = ""

    user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    call_echo(["scp", file, f"{user_host}:{dst}"])

    return dst


def _interactive_login_wrapper(args=[], **kwargs):
    input_ = get_variable("SSH_INTERACTIVE_LOGIN")
    ps = subprocess.Popen(args, stdin=subprocess.PIPE if input_ else None, **kwargs)
    if input_:
        ps.stdin.write(input_.encode() + b"\n")
        ps.stdin.close()

    ps.wait()
    if ps.poll() != 0:
        raise Exception("Non-zero return code.")


def _get_putty_credential():
    ssh_pwd = get_variable("SSH_PWD")
    if ssh_pwd:
        return ["-pw", ssh_pwd]
    else:
        return []


def push_file_putty(src, dest=None, user_host=None):
    if user_host is None:
        user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    if not dest:
        dest = "/home/%s/%s" % (get_variable("SSH_USER"), os.path.basename(src))

    args = ["pscp"] + _get_putty_credential()
    args += [src, f"{user_host}:{dest}"]

    _interactive_login_wrapper(args)


def pull_file_putty(src, dest=None, ssh_pwd=None, user_host=None):
    if dest is None:
        dest = os.getcwd()

    if user_host is None:
        user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    args = ["pscp"] + _get_putty_credential() + [user_host + ":" + src, dest]
    _interactive_login_wrapper(args)


def run_bash_script_putty(bash_script_file, user_host=None):
    if user_host is None:
        user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    # plink is preferred for automation.
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    args = ["plink", "-ssh", "-t", "-no-antispoof", user_host, "-m", bash_script_file]
    args += _get_putty_credential()
    _interactive_login_wrapper(args)


def run_bash_script_ssh(bash_script_file, user_host, wsl=False):
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
        f"vagrant upload {bash_script_file} /tmp/tmp_script.sh {vagrant_id}"
    )
    call_echo(f'vagrant ssh -c "bash /tmp/tmp_script.sh" {vagrant_id}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", help="command", type=str, default=None)
    args = parser.parse_args()

    if args.command:
        s = args.command

    else:
        script_file = os.environ["_SCRIPT"]
        assert script_file.endswith(".sh")
        script = Script(script_file)
        s = script.render()

    tmp_script_file = write_temp_file(s, ".sh")

    # Prerequisites: SSH_HOST, SSH_USER and SSH_PWD
    run_bash_script_putty(tmp_script_file)
