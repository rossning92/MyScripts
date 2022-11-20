import argparse
import os
import subprocess

from _pkgmanager import require_package
from _script import Script, find_script, get_variable
from _shutil import call_echo, convert_to_unix_path, write_temp_file


def _get_user_host():
    user_host = "%s@%s" % (
        os.environ.get("SSH_USER", get_variable("SSH_USER")),
        os.environ.get("SSH_HOST", get_variable("SSH_HOST")),
    )
    return user_host


def _get_port():
    return os.environ.get("SSH_PORT", get_variable("SSH_PORT"))


def _putty_wrapper(command, extra_args=[], **kwargs):
    require_package("putty")

    args = [command]
    port = _get_port()
    if port:
        args += ["-P", port]

    pwd = get_variable("SSH_PWD")
    if pwd:
        args += ["-pw", pwd]

    args += extra_args

    simulate_input = get_variable("SSH_INTERACTIVE_LOGIN")
    ps = subprocess.Popen(
        args, stdin=subprocess.PIPE if simulate_input else None, **kwargs
    )
    if simulate_input:
        ps.stdin.write(simulate_input.encode() + b"\n")
        ps.stdin.close()

    ps.wait()
    if ps.poll() != 0:
        raise Exception("Non-zero return code.")


def push_file_ssh(file, dest=None):
    if dest is None:
        dest = ""

    call_echo(["scp", file, "{}:{}".format(_get_user_host(), dest)])

    return dest


def push_file_putty(src, dest=None):
    if not dest:
        dest = "/home/%s/%s" % (get_variable("SSH_USER"), os.path.basename(src))

    _putty_wrapper("pscp", [src, "{}:{}".format(_get_user_host(), dest)])


def pull_file_putty(src, dest=None):
    if dest is None:
        dest = os.getcwd()

    _putty_wrapper("pscp", [_get_user_host() + ":" + src, dest])


def run_bash_script_putty(bash_script_file):
    # plink is preferred for automation.
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    _putty_wrapper(
        "plink",
        [
            "-ssh",
            "-t",
            "-no-antispoof",
            _get_user_host(),
            "-m",
            bash_script_file,
        ],
    )


def run_bash_script_ssh(bash_script_file, wsl=True):
    args = []
    if wsl:
        args += ["wsl"]
    args += ["scp"]
    port = _get_port()
    if port:
        args += ["-P", port]
    args += [  # src file
        convert_to_unix_path(bash_script_file, wsl=True) if wsl else bash_script_file
    ]
    args += [_get_user_host() + ":/tmp/s.sh"]  # dest
    call_echo(args)

    # -t : interactive session
    # source ~/.bash_profile ;
    args = []
    if wsl:
        args += ["wsl"]
    args += ["ssh", "-t", _get_user_host()]
    port = _get_port()
    if port:
        args += ["-p", port]
    args += ["bash /tmp/s.sh"]
    call_echo(args)
    # if wait_key("press any key to pause...", timeout=5):
    #     input("press any key to exit...")


def run_bash_script_vagrant(bash_script_file, vagrant_id):
    call_echo(f"vagrant upload {bash_script_file} /tmp/tmp_script.sh {vagrant_id}")
    call_echo(f'vagrant ssh -c "bash /tmp/tmp_script.sh" {vagrant_id}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", help="command", type=str, default=None)
    args = parser.parse_args()

    s = ""

    # ANDROID_SERIAL
    android_serial = get_variable("ANDROID_SERIAL")
    if android_serial:
        s += "export ANDROID_SERIAL=%s\n" % android_serial

    if args.command:
        s += args.command

    else:
        script_file = os.environ["SCRIPT"]
        assert script_file.endswith(".sh")
        script_file = find_script(script_file)

        script = Script(script_file)
        s += script.render()

    tmp_script_file = write_temp_file(s, ".sh")

    # Prerequisites: SSH_HOST, SSH_USER, SSH_PORT and SSH_PWD
    run_bash_script_putty(tmp_script_file)
