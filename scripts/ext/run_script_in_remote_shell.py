import os

from _script import Script, get_variable, update_script_access_time
from _shutil import (
    activate_window_by_name,
    call_echo,
    convert_to_unix_path,
    write_temp_file,
)

if __name__ == "__main__":
    script_path = os.environ["SCRIPT"]

    script = Script(script_path)
    update_script_access_time(script)

    s = ""  # script to run in remote shell

    # Default android device
    android_serial = get_variable("ANDROID_SERIAL")
    if android_serial:
        s += "export ANDROID_SERIAL=%s\n" % android_serial

    s += script.render()
    s += "\n"

    tmp_script_file = write_temp_file(s, ".sh")

    if script.ext != ".sh":
        print("Script type is not supported: %s" % script.ext)
        exit(0)

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

    # Ctrl-C
    call_echo(
        [
            "wsl",
            "bash",
            "-c",
            "export SCREENDIR=$HOME/.screen;"
            "screen -d -X stuff ^C;"  # -d indicates attached screen sessions
            "screen -d -X msgwait 0;"
            "screen -d -X readbuf %s;"
            "screen -d -X paste ." % convert_to_unix_path(tmp_file, wsl=True),
        ],
        shell=False,
    )

    activate_window_by_name("r/linux/remote_shell")
