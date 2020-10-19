from _script import *

if __name__ == "__main__":
    script_path = os.environ["_SCRIPT_PATH"]

    script = ScriptItem(script_path)
    update_script_acesss_time(script)

    s = script.render() + "\n"
    tmp_script_file = write_temp_file(s, ".sh")

    if script.ext != ".sh":
        print("Script type is not supported: %s" % script.ext)
        exit(0)

    # Ctrl-C
    call_echo(["wsl", "screen", "-S", "ssh_session", "-X", "stuff", "^C"], shell=False)
    call_echo(["wsl", "screen", "-S", "ssh_session", "-X", "msgwait", "0"], shell=False)

    # Write shell commands to paste buffer
    lines = [
        "cat > /tmp/script.sh <<'__EOF__'",
        *s.splitlines(),
        "__EOF__",
        "clear",
        "bash /tmp/script.sh",
    ]
    tmp_file = write_temp_file("\n".join(lines) + "\n", "pastebuf.txt")
    call_echo(
        [
            "wsl",
            "screen",
            "-S",
            "ssh_session",
            "-X",
            "readbuf",
            convert_to_unix_path(tmp_file, wsl=True),
        ],
        shell=False,
    )
    exec_ahk("WinActivate r/linux/ssh")
    call_echo(["wsl", "screen", "-S", "ssh_session", "-X", "paste", "."], shell=False)
