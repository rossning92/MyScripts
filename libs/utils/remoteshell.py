import logging
import os
import subprocess
import sys

from _pkgmanager import require_package
from _script import Script, get_variable
from _shutil import (
    call_echo,
    convert_to_unix_path,
    quote_arg,
    write_temp_file,
)

from .window import activate_window_by_name


def run_bash_script_in_remote_shell(script_path, send_prev_job_to_background=False):
    ext = os.path.splitext(script_path)[1]
    if ext != ".sh" and ext != ".txt":
        print("Script type is not supported: %s" % ext)
        exit(0)

    script = Script(script_path)

    # Default android device
    if ext == ".sh":
        s = ""  # bash commands

        android_serial = get_variable("ANDROID_SERIAL")
        if android_serial:
            s += "export ANDROID_SERIAL=%s\n" % android_serial

        # Passing variables through environmental variable
        for name, val in script.get_variables().items():
            # Override with enviromental variables
            if name in os.environ:
                val = os.environ[name]
            s += "export %s=%s\n" % (name, quote_arg(val, shell_type="bash"))
        s += "\n"

        s += script.render()
        s += "\n"

        # Write shell commands to paste buffer
        lines = [
            "",
            "cat >~/s.sh <<'__EOF__'",
            *s.splitlines(),
            "__EOF__",
            "clear",
            "bash ~/s.sh",
        ]
        tmp_file = write_temp_file("\n".join(lines) + "\n", "pastebuf.txt")

    else:
        tmp_file = write_temp_file(script.render(), "pastebuf.txt")

    args = []
    if sys.platform == "win32":
        args.append("wsl")
    args += [
        "bash",
        "-c",
    ]
    args.append(
        ("export SCREENDIR=$HOME/.screen;" if sys.platform == "win32" else "")
        + (
            # -d: indicates attached screen sessions
            # ^C: send Ctrl-C
            "screen -d -X stuff ^Z^Mbg^M;"
            if send_prev_job_to_background
            else "screen -d -X stuff ^C;" if ext == ".sh" else ""
        )
        + (
            "screen -d -X msgwait 0;"
            "screen -d -X readbuf %s;"
            "screen -d -X paste ." % convert_to_unix_path(tmp_file, wsl=True)
        ),
    )

    call_echo(
        args,
        shell=False,
    )

    activate_window_by_name("remote_shell")


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


def _get_pwd(pwd=None):
    if pwd:
        return pwd
    else:
        return os.environ.get("SSH_PWD", get_variable("SSH_PWD"))


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

    pwd = _get_pwd(pwd)
    if pwd:
        args += ["-pw", pwd]

    args += extra_args

    simulate_input = get_variable("SSH_INTERACTIVE_LOGIN")
    logging.debug(args)
    ps = subprocess.Popen(args, stdin=subprocess.PIPE if simulate_input else None)
    if simulate_input:
        ps.stdin.write(simulate_input.encode() + b"\n")
        ps.stdin.close()

    ps.wait()
    if ps.poll() != 0:
        raise Exception("Non-zero return code.")


def push_file_ssh(src, dest, user=None, host=None, pwd=None):
    args = []

    pwd = _get_pwd(pwd)
    if pwd:
        require_package("sshpass")
        args += ["sshpass", "-p", pwd]

    args += ["scp", src, "{}:{}".format(_get_user_host(user=user, host=host), dest)]

    call_echo(args)

    return dest


def push_file_putty(src, dest=None, user=None, host=None, pwd=None):
    _putty_wrapper(
        "pscp",
        [src, "{}:{}".format(_get_user_host(user=user, host=host), dest)],
        pwd=pwd,
    )


def push_file(src, dest=None, user=None, host=None, pwd=None):
    if not dest:
        dest = "/home/%s/%s" % (_get_user(user), os.path.basename(src))
    if sys.platform == "win32":
        push_file_putty(src=src, dest=dest, user=user, host=host, pwd=pwd)
    else:
        push_file_ssh(src=src, dest=dest, user=user, host=host, pwd=pwd)


def pull_file_putty(src, dest=None):
    if dest is None:
        dest = os.getcwd()

    _putty_wrapper("pscp", [_get_user_host() + ":" + src, dest])


def pull_file_ssh(src, dest=None, port=None):
    if dest is None:
        dest = os.getcwd()

    args = [
        "scp",
        "-o",
        "StrictHostKeyChecking=no",
    ]

    args += ["-P", _get_port(port)]
    args += [
        "{}:{}".format(_get_user_host(), src),
        dest,
    ]

    call_echo(args)

    return dest


def run_bash_script_putty(bash_script_file, user=None, host=None, pwd=None, port=None):
    # plink is preferred for automation.
    # -t: switch to force a use of an interactive session
    # -no-antispoof: omit anti-spoofing prompt after authentication
    _putty_wrapper(
        "plink",
        [
            # "-no-antispoof",
            "-ssh",
            "-t",
            _get_user_host(user=user, host=host),
            "-m",
            bash_script_file,
        ],
        pwd=pwd,
        port=port,
    )


def run_bash_script_openssh(
    bash_script_file, wsl=True, user=None, host=None, pwd=None, port=None
):
    with open(bash_script_file, "r", encoding="utf-8") as f:
        command: str = f.read()

    args = []

    # wsl
    if wsl and sys.platform == "win32":
        args += ["wsl"]

    # pwd
    pwd = _get_pwd(pwd)
    if pwd:
        require_package("sshpass")
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


def run_bash_script_ssh(file, wsl=True, user=None, host=None, pwd=None, port=None):
    if sys.platform == "win32":
        run_bash_script_putty(file, user=user, host=host, pwd=pwd)
    else:
        run_bash_script_openssh(file, user=user, host=host, pwd=pwd)
