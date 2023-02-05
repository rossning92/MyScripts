import argparse
import os
import subprocess
import sys

from _pkgmanager import require_package
from _script import Script, find_script, get_variable
from _shutil import call_echo, convert_to_unix_path, write_temp_file


def _get_user(user=None):
    if user:
        return user
    else:
        return os.environ.get("SSH_USER", get_variable("SSH_USER"))


def _get_host(host=None):
    if host:
        return host
    else:
        return os.environ.get("SSH_HOST", get_variable("SSH_HOST"))


def _get_user_host(user=None, host=None):
    return "%s@%s" % (
        _get_user(user),
        _get_host(host),
    )


def _get_port(port=None):
    if port:
        return port
    else:
        return os.environ.get("SSH_PORT", get_variable("SSH_PORT"))


def _putty_wrapper(command, extra_args=[], pwd=None, port=None):
    require_package("putty")

    args = [command]
    port = _get_port(port=port)
    if port:
        args += ["-P", port]

    pwd = os.environ.get("SSH_PWD", get_variable("SSH_PWD"))
    if pwd:
        args += ["-pw", pwd]

    args += extra_args

    simulate_input = get_variable("SSH_INTERACTIVE_LOGIN")
    ps = subprocess.Popen(args, stdin=subprocess.PIPE if simulate_input else None)
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


def push_file_putty(src, dest=None, user=None, host=None, pwd=None):
    if not dest:
        dest = "/home/%s/%s" % (_get_user(user), os.path.basename(src))

    _putty_wrapper(
        "pscp",
        [src, "{}:{}".format(_get_user_host(user=user, host=host), dest)],
        pwd=pwd,
    )


def pull_file_putty(src, dest=None):
    if dest is None:
        dest = os.getcwd()

    _putty_wrapper("pscp", [_get_user_host() + ":" + src, dest])


def run_bash_script_putty(bash_script_file, user=None, host=None, pwd=None, port=None):
    # plink is preferred for automation.
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    _putty_wrapper(
        "plink",
        [
            "-ssh",
            "-t",
            "-no-antispoof",
            _get_user_host(user=user, host=host),
            "-m",
            bash_script_file,
        ],
        pwd=pwd,
        port=port,
    )


def run_bash_script_ssh(
    bash_script_file, wsl=True, user=None, host=None, pwd=None, port=None
):
    with open(bash_script_file, "r", encoding="utf-8") as f:
        command: str = f.read()

    args = []

    # wsl
    if wsl and sys.platform == "win32":
        args += ["wsl"]

    # pwd
    if pwd:
        args += ["sshpass", "-p", pwd]

    args += [
        "ssh",
        "-o",
        "StrictHostKeyChecking=no",  # disable host key checking
        "-t",  # interactive session
        _get_user_host(user=user, host=host),
    ]

    port = _get_port(port=port)
    if port:
        args += ["-p", port]

    if wsl:
        command = command.replace("$", "\\$")  # avoid variable expansion
    args += [command]
    subprocess.check_call(args)


def run_bash_script_vagrant(bash_script_file, vagrant_id):
    call_echo(f"vagrant upload {bash_script_file} /tmp/tmp_script.sh {vagrant_id}")
    call_echo(f'vagrant ssh -c "bash /tmp/tmp_script.sh" {vagrant_id}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", type=str, default=None)
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--user", type=str, default=None)
    parser.add_argument("--pwd", type=str, default=None)
    parser.add_argument("file", type=str, nargs="?", default=None)

    args = parser.parse_args()

    bash_commands = ""

    # ANDROID_SERIAL
    android_serial = get_variable("ANDROID_SERIAL")
    if android_serial:
        bash_commands += "export ANDROID_SERIAL=%s\n" % android_serial

    if args.command:
        bash_commands += args.command

    elif args.file:
        file = args.file
        with open(file, "r", encoding="utf-8") as f:
            bash_commands += f.read() + "\n"

    else:
        file = os.environ["SCRIPT"]
        assert file.endswith(".sh")
        file = find_script(file)

        script = Script(file)
        bash_commands += script.render()

    tmp_file = write_temp_file(bash_commands, ".sh")

    # Prerequisites: SSH_HOST, SSH_USER, SSH_PORT and SSH_PWD
    run_bash_script_ssh(tmp_file, user=args.user, host=args.host, pwd=args.pwd)
