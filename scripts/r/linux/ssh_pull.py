from _shutil import *

src = r"{{_SRC_FILE}}"

call_echo(
    [
        "pscp",
        "-pw",
        "{{SSH_PWD}}",
        "{{SSH_USER}}@{{SSH_HOST}}:" + src,
        os.path.expanduser("~/Desktop"),
    ]
)
