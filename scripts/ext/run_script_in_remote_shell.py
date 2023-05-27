import argparse
import os
import sys

from _script import Script, get_variable, update_script_access_time
from _shutil import (
    activate_window_by_name,
    call_echo,
    convert_to_unix_path,
    quote_arg,
    write_temp_file,
)


def run_bash_script_in_remote_shell(script_path):
    script = Script(script_path)
    # update_script_access_time(script)

    s = ""  # script to run in remote shell

    # Default android device
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

    args = []
    if sys.platform == "win32":
        args.append("wsl")
    args += [
        "bash",
        "-c",
    ]
    args.append(
        ("export SCREENDIR=$HOME/.screen;" if sys.platform == "win32" else "")
        + "export;screen -d -X stuff ^C;"  # -d indicates attached screen sessions, send Ctrl-C
        "screen -d -X msgwait 0;"
        "screen -d -X readbuf %s;"
        "screen -d -X paste ." % convert_to_unix_path(tmp_file, wsl=True),
    )

    call_echo(
        args,
        shell=False,
    )

    activate_window_by_name("remote_shell")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=str, nargs="?", default=None)
    args = parser.parse_args()

    if args.file:
        script_path = args.file
    else:
        script_path = os.environ["SCRIPT"]

    ext = os.path.splitext(script_path)[1]
    if ext != ".sh":
        print("Script type is not supported: %s" % ext)
        exit(0)

    run_bash_script_in_remote_shell(script_path)
