from _script import get_variable
from _shutil import call_echo, get_files


def push_file(file, dst=None):
    if dst is None:
        dst = ""

    ssh_pwd = get_variable("SSH_PWD")
    user_host = "%s@%s" % (get_variable("SSH_USER"), get_variable("SSH_HOST"))

    call_echo(["pscp", "-pw", ssh_pwd, file, f"{user_host}:{dst}"])

    return dst


if __name__ == "__main__":
    if "{{_DST_DIR}}":
        dst = "{{_DST_DIR}}"
    else:
        dst = "/home/{{SSH_USER}}"

    file = get_files()[0]
    push_file(file, dst)
